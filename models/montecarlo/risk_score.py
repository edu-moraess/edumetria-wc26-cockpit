"""
models/montecarlo/risk_score.py
World Cup Risk Score (0-100) — índice composto de risco macro/geopolítico,
construído 100% a partir de dados já disponíveis no banco (yfinance/FRED).

Componentes (cada um normalizado 0-100, onde 100 = risco máximo):
- VIX            : volatilidade implícita do mercado (risco financeiro)
- Petróleo (WTI) : desvio do preço atual vs. média móvel de 1 ano
                    (choques de oferta/geopolítica no Oriente Médio)
- FX_INDEX       : volatilidade recente do dólar (estresse cambial)

Metodologia de normalização: percentil histórico do valor mais recente
dentro da própria série (janela disponível).

SANITY CHECKS: cada componente valida se o valor mais recente está
dentro de uma faixa plausível. Se não estiver, o componente é marcado
como "suspeito" e EXCLUÍDO do cálculo (em vez de distorcer o score
silenciosamente). Isso evita que dados desatualizados/inconsistentes
do yfinance gerem classificações de risco enganosas.

Uso:
    python -m models.montecarlo.risk_score
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.connection import get_connection  # noqa: E402

RISK_WEIGHTS = {
    "vix": 0.40,
    "oil_shock": 0.35,
    "fx_volatility": 0.25,
}

# Faixas plausíveis para sanity check do valor MAIS RECENTE de cada série.
# Fora dessa faixa => dado provavelmente desatualizado/inconsistente.
PLAUSIBLE_RANGES = {
    "VIX": (5, 100),
    "WTI_CRUDE": (15, 150),       # US$/bbl
    "FX_INDEX": (80, 160),        # índice DTWEXBGS, base jan/2006=100
}


def _load_series(indicator_code: str, country_code: str | None = None) -> pd.Series:
    with get_connection() as conn:
        if country_code:
            df = conn.execute(
                """
                SELECT period, value FROM fact_indicator_values
                WHERE indicator_code = ? AND country_code = ?
                ORDER BY period
                """,
                [indicator_code, country_code],
            ).df()
        else:
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
    return df.set_index("period")["value"]


def _percentile_score(series: pd.Series) -> float | None:
    """Retorna o percentil (0-100) do último valor na distribuição histórica."""
    if series.empty or len(series) < 30:
        return None
    last_value = series.iloc[-1]
    return float((series < last_value).mean() * 100)


def _check_plausible(indicator_code: str, value: float | None) -> bool:
    """Retorna True se o valor está dentro da faixa plausível (ou se não há faixa definida)."""
    if value is None:
        return False
    low, high = PLAUSIBLE_RANGES.get(indicator_code, (float("-inf"), float("inf")))
    return low <= value <= high


def score_vix() -> tuple[float | None, dict]:
    """Score VIX: percentil do nível atual na própria distribuição histórica."""
    series = _load_series("VIX")
    detail = {
        "current_value": float(series.iloc[-1]) if not series.empty else None,
        "last_date": series.index[-1].strftime("%Y-%m-%d") if not series.empty else None,
        "n_observations": len(series),
    }

    if not _check_plausible("VIX", detail["current_value"]):
        detail["status"] = "suspeito (fora da faixa plausível)"
        return None, detail

    score = _percentile_score(series)
    detail["status"] = "ok"
    return score, detail


def score_oil_shock() -> tuple[float | None, dict]:
    """
    Score de choque no petróleo: desvio % do preço atual (WTI) vs. média
    móvel de 252 dias (≈1 ano), normalizado via percentil histórico
    desse desvio absoluto.
    """
    series = _load_series("WTI_CRUDE")

    detail = {
        "current_value": float(series.iloc[-1]) if not series.empty else None,
        "last_date": series.index[-1].strftime("%Y-%m-%d") if not series.empty else None,
        "n_observations": len(series),
    }

    if not _check_plausible("WTI_CRUDE", detail["current_value"]):
        detail["status"] = "suspeito (fora da faixa plausível US$15-150/bbl)"
        return None, detail

    if len(series) < 252:
        detail["status"] = "insuficiente (< 252 observações)"
        return None, detail

    rolling_mean = series.rolling(window=252).mean()
    deviation = (series - rolling_mean) / rolling_mean * 100
    deviation = deviation.dropna()

    if deviation.empty:
        detail["status"] = "insuficiente (desvio não calculável)"
        return None, detail

    score = _percentile_score(deviation.abs())
    detail["deviation_pct"] = float(deviation.iloc[-1])
    detail["status"] = "ok"
    return score, detail


def score_fx_volatility() -> tuple[float | None, dict]:
    """
    Score de volatilidade cambial: volatilidade realizada (desvio padrão
    dos retornos diários, janela de 21 dias) do índice FX_INDEX (USD
    trade-weighted, FRED), normalizada via percentil histórico.
    """
    series = _load_series("FX_INDEX", country_code="USA")

    detail = {
        "current_value": float(series.iloc[-1]) if not series.empty else None,
        "last_date": series.index[-1].strftime("%Y-%m-%d") if not series.empty else None,
        "n_observations": len(series),
    }

    if not _check_plausible("FX_INDEX", detail["current_value"]):
        detail["status"] = "suspeito (fora da faixa plausível 80-160)"
        return None, detail

    if len(series) < 60:
        detail["status"] = "insuficiente (< 60 observações)"
        return None, detail

    returns = series.pct_change().dropna()
    rolling_vol = returns.rolling(window=21).std()
    rolling_vol = rolling_vol.dropna()

    if rolling_vol.empty:
        detail["status"] = "insuficiente (vol. não calculável)"
        return None, detail

    score = _percentile_score(rolling_vol)
    detail["realized_vol_21d"] = float(rolling_vol.iloc[-1])
    detail["status"] = "ok"
    return score, detail


COMPONENT_FUNCS = {
    "vix": score_vix,
    "oil_shock": score_oil_shock,
    "fx_volatility": score_fx_volatility,
}


def classify_risk(score: float) -> str:
    if score < 25:
        return "Baixo"
    elif score < 50:
        return "Moderado"
    elif score < 75:
        return "Elevado"
    else:
        return "Crítico"


def calculate_risk_score() -> dict:
    """
    Calcula o World Cup Risk Score (0-100) combinando os componentes
    disponíveis e plausíveis. Componentes ausentes ou suspeitos têm
    peso redistribuído proporcionalmente entre os demais.
    """
    components = {}
    for name, func in COMPONENT_FUNCS.items():
        score, detail = func()
        components[name] = {"score": score, "detail": detail}

    available = {k: v["score"] for k, v in components.items() if v["score"] is not None}

    if not available:
        risk_score = None
        classification = "Indisponível"
        completeness = 0.0
    else:
        weight_sum = sum(RISK_WEIGHTS[k] for k in available)
        risk_score = sum(
            available[k] * (RISK_WEIGHTS[k] / weight_sum) for k in available
        )
        classification = classify_risk(risk_score)
        completeness = weight_sum * 100

    return {
        "risk_score": risk_score,
        "classification": classification,
        "completeness_pct": completeness,
        "components": components,
    }


def run():
    print("World Cup Risk Score — cálculo\n")
    result = calculate_risk_score()

    for name, data in result["components"].items():
        score = data["score"]
        status = f"{score:.1f}" if score is not None else "excluído"
        print(f"  {name:15s}: percentil={status}  detalhe={data['detail']}")

    if result["risk_score"] is not None:
        print(f"\nRisk Score: {result['risk_score']:.1f} ({result['classification']})")
    else:
        print("\nRisk Score: indisponível (sem dados suficientes/plausíveis)")

    print(f"Completeness: {result['completeness_pct']:.0f}%")


if __name__ == "__main__":
    run()