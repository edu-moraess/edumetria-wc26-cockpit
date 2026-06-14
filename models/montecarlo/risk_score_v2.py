"""
models/montecarlo/risk_score_v2.py
World Cup Risk Score 2.0 — framework multicamadas.

DIMENSÕES:
  Financeira  (peso 35%): VIX, MOVE Index, HY Spread, TED Spread
  Energética  (peso 25%): WTI, Brent, Natural Gas
  Macro       (peso 25%): Yield Spread 10Y-2Y, 10Y-3M, Leading Index
  Geopolítica (peso 15%): placeholder (Geopolitical Risk Index — pendente)

METODOLOGIA:
  Cada componente é normalizado via percentil histórico (0-100) da série
  disponível no banco. O score de cada dimensão é a média ponderada dos
  componentes disponíveis (peso redistribuído entre os presentes).
  O score final é a média ponderada das dimensões.

LIMITAÇÕES:
  - Geopolitical Risk Index (Caldara & Iacoviello) não tem API gratuita
    automática — dimensão geopolítica usa placeholder até integração manual
  - MOVE Index pode não estar disponível via yfinance (^MOVE) — substituído
    por TED Spread como proxy de stress de bonds quando ausente
  - Percentil histórico é sensível ao tamanho da janela disponível
    (min. 30 observações por componente)

REFERÊNCIA:
  Caldara, D. & Iacoviello, M. (2022). "Measuring Geopolitical Risk."
  American Economic Review. Para uso futuro quando dataset disponível.

Uso:
    python -m models.montecarlo.risk_score_v2
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.connection import get_connection  # noqa: E402

# ------------------------------------------------------------------
# ESTRUTURA MULTICAMADAS
# ------------------------------------------------------------------
DIMENSIONS = {
    "financeira": {
        "weight": 0.35,
        "label": "Financeira",
        "components": {
            "VIX":        {"weight": 0.40, "label": "VIX",              "higher_is_riskier": True},
            "MOVE_INDEX": {"weight": 0.25, "label": "MOVE Index",       "higher_is_riskier": True},
            "HY_SPREAD":  {"weight": 0.20, "label": "High Yield Spread","higher_is_riskier": True},
            "TED_SPREAD": {"weight": 0.15, "label": "TED Spread",       "higher_is_riskier": True},
        },
    },
    "energetica": {
        "weight": 0.25,
        "label": "Energética",
        "components": {
            "WTI_CRUDE":   {"weight": 0.45, "label": "WTI (choque)",    "higher_is_riskier": True,  "use_deviation": True},
            "BRENT_CRUDE": {"weight": 0.35, "label": "Brent (choque)",  "higher_is_riskier": True,  "use_deviation": True},
            "NATURAL_GAS": {"weight": 0.20, "label": "Gás Natural",     "higher_is_riskier": True,  "use_deviation": True},
        },
    },
    "macro": {
        "weight": 0.25,
        "label": "Macroeconômica",
        "components": {
            "YIELD_SPREAD_10Y2Y": {"weight": 0.40, "label": "Spread 10Y-2Y",  "higher_is_riskier": False},
            "YIELD_SPREAD_10Y3M": {"weight": 0.35, "label": "Spread 10Y-3M",  "higher_is_riskier": False},
            "LEADING_INDEX":      {"weight": 0.25, "label": "Leading Index",   "higher_is_riskier": False},
        },
    },
    "geopolitica": {
        "weight": 0.15,
        "label": "Geopolítica",
        "components": {
            # Placeholder — Geopolitical Risk Index (Caldara & Iacoviello)
            # será integrado manualmente quando dataset disponível
        },
    },
}

PLAUSIBLE_RANGES = {
    "VIX":                (5,    100),
    "MOVE_INDEX":         (30,   300),
    "HY_SPREAD":          (1.5,  25),
    "TED_SPREAD":         (0.01, 5),
    "WTI_CRUDE":          (15,   150),
    "BRENT_CRUDE":        (15,   150),
    "NATURAL_GAS":        (1,    20),
    "YIELD_SPREAD_10Y2Y": (-3,   4),
    "YIELD_SPREAD_10Y3M": (-3,   4),
    "LEADING_INDEX":      (-5,   5),
}


def _load_series(indicator_code: str) -> pd.Series:
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value FROM fact_indicator_values
            WHERE indicator_code = ?
            ORDER BY period
            """,
            [indicator_code],
        ).df()
    if df.empty:
        return pd.Series(dtype=float)
    df["period"] = pd.to_datetime(df["period"])
    s = df.set_index("period")["value"]
    return s[~s.index.duplicated(keep="last")].dropna()


def _check_plausible(code: str, value: float | None) -> bool:
    if value is None:
        return False
    lo, hi = PLAUSIBLE_RANGES.get(code, (float("-inf"), float("inf")))
    return lo <= value <= hi


def _percentile_score(series: pd.Series, higher_is_riskier: bool = True) -> float | None:
    if len(series) < 30:
        return None
    last = series.iloc[-1]
    pct  = float((series < last).mean() * 100)
    return pct if higher_is_riskier else (100 - pct)


def _deviation_score(series: pd.Series, window: int = 252) -> float | None:
    """Score baseado no desvio absoluto vs. média móvel (para commodities)."""
    if len(series) < window:
        return None
    rolling_mean = series.rolling(window=window).mean()
    deviation    = (series - rolling_mean) / rolling_mean * 100
    deviation    = deviation.abs().dropna()
    if deviation.empty:
        return None
    return _percentile_score(deviation, higher_is_riskier=True)


def compute_component(code: str, cfg: dict) -> dict:
    """Calcula o score de um único componente."""
    series = _load_series(code)

    detail = {
        "current_value": float(series.iloc[-1]) if not series.empty else None,
        "last_date":     series.index[-1].strftime("%Y-%m-%d") if not series.empty else None,
        "n_obs":         len(series),
        "status":        "ok",
    }

    if not _check_plausible(code, detail["current_value"]):
        detail["status"] = "suspeito"
        return {"score": None, "detail": detail}

    if cfg.get("use_deviation"):
        score = _deviation_score(series)
        if score is not None and not series.empty:
            rolling_mean = series.rolling(252).mean()
            deviation    = (series - rolling_mean) / rolling_mean * 100
            detail["deviation_pct"] = float(deviation.dropna().iloc[-1]) if not deviation.dropna().empty else None
    else:
        score = _percentile_score(series, cfg.get("higher_is_riskier", True))

    if score is None:
        detail["status"] = "insuficiente"

    return {"score": score, "detail": detail}


def calculate_dimension(dim_name: str, dim_cfg: dict) -> dict:
    """Calcula o score de uma dimensão (média ponderada dos componentes disponíveis)."""
    components = {}
    for code, cfg in dim_cfg["components"].items():
        components[code] = compute_component(code, cfg)

    available = {c: v for c, v in components.items() if v["score"] is not None}

    if not available:
        return {
            "score":          None,
            "completeness":   0.0,
            "components":     components,
        }

    weight_sum = sum(dim_cfg["components"][c]["weight"] for c in available)
    score = sum(
        available[c]["score"] * (dim_cfg["components"][c]["weight"] / weight_sum)
        for c in available
    )
    completeness = weight_sum  # fração dos pesos cobertos

    return {
        "score":        score,
        "completeness": completeness,
        "components":   components,
    }


def calculate_risk_score_v2() -> dict:
    """
    Calcula o World Cup Risk Score 2.0 multicamadas.
    Retorna estrutura completa para visualização no dashboard.
    """
    dimensions = {}
    for dim_name, dim_cfg in DIMENSIONS.items():
        dimensions[dim_name] = {
            "label":  dim_cfg["label"],
            "weight": dim_cfg["weight"],
            **calculate_dimension(dim_name, dim_cfg),
        }

    available_dims = {k: v for k, v in dimensions.items() if v["score"] is not None}

    if not available_dims:
        return {
            "risk_score":       None,
            "classification":   "Indisponível",
            "completeness_pct": 0.0,
            "dimensions":       dimensions,
        }

    weight_sum = sum(dimensions[k]["weight"] for k in available_dims)
    risk_score = sum(
        available_dims[k]["score"] * (dimensions[k]["weight"] / weight_sum)
        for k in available_dims
    )
    completeness = weight_sum * 100

    if risk_score < 25:   classification = "Baixo"
    elif risk_score < 50: classification = "Moderado"
    elif risk_score < 75: classification = "Elevado"
    else:                 classification = "Crítico"

    return {
        "risk_score":       risk_score,
        "classification":   classification,
        "completeness_pct": completeness,
        "dimensions":       dimensions,
    }


def run():
    print("World Cup Risk Score 2.0 — Multicamadas\n")
    result = calculate_risk_score_v2()

    for dim_name, dim in result["dimensions"].items():
        score_str = f"{dim['score']:.1f}" if dim["score"] is not None else "—"
        print(f"  [{dim['label']}] score={score_str} completeness={dim['completeness']:.0%}")
        for code, comp in dim.get("components", {}).items():
            s = comp["score"]
            print(f"    {code:25s}: {'%.1f' % s if s is not None else 'excluído'}")

    print(f"\nRisk Score 2.0: {result['risk_score']:.1f if result['risk_score'] else '—'} "
          f"({result['classification']})")
    print(f"Completeness  : {result['completeness_pct']:.0f}%")


if __name__ == "__main__":
    run()