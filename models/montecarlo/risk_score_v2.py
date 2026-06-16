"""
models/montecarlo/risk_score_v2.py — v3 CORRIGIDO
World Cup Risk Score 2.0 — framework multicamadas.

CORREÇÕES v3:
- REMOVIDO TED Spread (descontinuado em jan/2023)
- ADICIONADO SOFR (Secured Overnight Financing Rate) como proxy de stress interbancário
- Validação de frescor: componentes com mais de 60 dias são marcados como 'desatualizados'
- Melhor redistribuição de pesos para componentes ausentes/velhos
"""

import sys
from pathlib import Path
from datetime import datetime

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
            "SOFR_RATE":  {"weight": 0.15, "label": "SOFR (Interbank)",  "higher_is_riskier": True},
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
        },
    },
}

PLAUSIBLE_RANGES = {
    "VIX":                (5,    100),
    "MOVE_INDEX":         (30,   300),
    "HY_SPREAD":          (1.5,  25),
    "SOFR_RATE":          (0.01, 10),
    "WTI_CRUDE":          (15,   150),
    "BRENT_CRUDE":        (15,   150),
    "NATURAL_GAS":        (1,    20),
    "YIELD_SPREAD_10Y2Y": (-3,   4),
    "YIELD_SPREAD_10Y3M": (-3,   4),
    "LEADING_INDEX":      (-5,   5),
}

MAX_DAYS_OLD = 60  # ✅ CORREÇÃO: Limite de frescor para o Risk Score


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
    if len(series) < window:
        return None
    rolling_mean = series.rolling(window=window).mean()
    deviation    = (series - rolling_mean) / rolling_mean * 100
    deviation    = deviation.abs().dropna()
    if deviation.empty:
        return None
    return _percentile_score(deviation, higher_is_riskier=True)


def compute_component(code: str, cfg: dict) -> dict:
    """Calcula o score de um único componente com validação de frescor."""
    series = _load_series(code)

    if series.empty:
        return {"score": None, "detail": {"status": "ausente", "current_value": None}}

    last_date = series.index[-1]
    days_old  = (datetime.now() - last_date).days
    current_value = float(series.iloc[-1])

    detail = {
        "current_value": current_value,
        "last_date":     last_date.strftime("%Y-%m-%d"),
        "days_old":      days_old,
        "n_obs":         len(series),
        "status":        "ok",
    }

    # ✅ CORREÇÃO: Validação de frescor
    if days_old > MAX_DAYS_OLD:
        detail["status"] = "desatualizado"
        return {"score": None, "detail": detail}

    if not _check_plausible(code, current_value):
        detail["status"] = "suspeito"
        return {"score": None, "detail": detail}

    if cfg.get("use_deviation"):
        score = _deviation_score(series)
        if score is not None:
            rolling_mean = series.rolling(252).mean()
            dev_val      = (series - rolling_mean) / rolling_mean * 100
            detail["deviation_pct"] = float(dev_val.dropna().iloc[-1]) if not dev_val.dropna().empty else None
    else:
        score = _percentile_score(series, cfg.get("higher_is_riskier", True))

    if score is None:
        detail["status"] = "insuficiente"

    return {"score": score, "detail": detail}


def calculate_dimension(dim_name: str, dim_cfg: dict) -> dict:
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
    
    return {
        "score":        score,
        "completeness": weight_sum,
        "components":   components,
    }


def calculate_risk_score_v2() -> dict:
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
    
    if risk_score < 25:   classification = "Baixo"
    elif risk_score < 50: classification = "Moderado"
    elif risk_score < 75: classification = "Elevado"
    else:                 classification = "Crítico"

    return {
        "risk_score":       risk_score,
        "classification":   classification,
        "completeness_pct": weight_sum * 100,
        "dimensions":       dimensions,
    }


def run():
    print("World Cup Risk Score 2.0 — Multicamadas (v3)\n")
    result = calculate_risk_score_v2()
    print(f"Risk Score 2.0: {result['risk_score']:.1f if result['risk_score'] else '—'} ({result['classification']})")
    print(f"Completeness  : {result['completeness_pct']:.0f}%\n")

    for dim_name, dim in result["dimensions"].items():
        score_str = f"{dim['score']:.1f}" if dim["score"] is not None else "—"
        print(f"  [{dim['label']}] score={score_str} completeness={dim['completeness']:.0%}")
        for code, comp in dim.get("components", {}).items():
            s = comp["score"]
            st = comp["detail"]["status"]
            val = comp["detail"].get("current_value")
            print(f"    {code:20s}: {s if s is not None else '—':8} status={st:12} val={val}")

if __name__ == "__main__":
    run()
