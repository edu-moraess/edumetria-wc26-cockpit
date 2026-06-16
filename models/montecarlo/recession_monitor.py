"""
models/montecarlo/recession_monitor.py
Recession Monitor — probabilidade de recessão nos EUA.

INDICADORES:
  1. Yield Spread 10Y-2Y  — inversão histórica precede recessão 12-18m
  2. Yield Spread 10Y-3M  — preferido pelo Fed NY como preditor de recessão
  3. Sahm Rule            — regra empírica: taxa de desemprego sobe 0.5pp
                            acima do mínimo dos últimos 12m → recessão
  4. Leading Index (USSLIND) — índice composto de 6 indicadores antecedentes
  5. RECESSION_PROB       — probabilidade oficial Fed NY (modelo probit)

SCORE COMPOSTO (0-100):
  Cada indicador é transformado em probabilidade de recessão (0-100%)
  e o score final é a média ponderada dos disponíveis.

SEMÁFORO:
  Verde   (<25): baixo risco
  Amarelo (25-50): atenção
  Laranja (50-75): elevado
  Vermelho (>75): crítico

REFERÊNCIAS:
  - Estrella, A. & Mishkin, F.S. (1998). "Predicting U.S. Recessions:
    Financial Variables as Leading Indicators." Review of Economics and
    Statistics 80(1): 45-61.
  - Sahm, C. (2019). "Direct Stimulus Payments to Individuals."
    Hamilton Project. (Sahm Rule original)
  - Federal Reserve Bank of New York — Yield Curve and Predicted GDP
    Growth: https://www.newyorkfed.org/research/capital_markets/ycfaq

Uso:
    python -m models.montecarlo.recession_monitor
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.connection import get_connection  # noqa: E402


def _load_series(indicator_code: str, country_code: str = "USA") -> pd.Series:
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value FROM fact_indicator_values
            WHERE indicator_code = ? AND country_code = ?
            ORDER BY period
            """,
            [indicator_code, country_code],
        ).df()
    if df.empty:
        return pd.Series(dtype=float)
    df["period"] = pd.to_datetime(df["period"])
    s = df.set_index("period")["value"]
    return s[~s.index.duplicated(keep="last")].dropna()


def _load_global(indicator_code: str) -> pd.Series:
    """Para indicadores sem country_code (NULL no banco)."""
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


def score_yield_spread_10y2y() -> dict:
    """
    Probabilidade de recessão baseada no spread 10Y-2Y.
    Proxy do modelo probit do Fed NY (versão simplificada):
    P(recessão) ≈ sigmoid(-1.0 * spread) * 100
    Inversão (spread < 0) → alta probabilidade.
    """
    series = _load_series("YIELD_SPREAD_10Y2Y")
    if series.empty:
        return {"prob": None, "current_value": None, "signal": "sem dados"}

    last = series.iloc[-1]
    # Aproximação sigmóide do modelo probit do Fed NY
    prob = float(1 / (1 + np.exp(1.5 * last)) * 100)

    if last < -0.5:   signal = "Inversão severa — alto risco"
    elif last < 0:    signal = "Curva invertida — risco elevado"
    elif last < 0.5:  signal = "Achatamento — atenção"
    else:             signal = "Normal"

    return {
        "prob":          prob,
        "current_value": float(last),
        "last_date":     series.index[-1].strftime("%b/%Y"),
        "signal":        signal,
        "n_obs":         len(series),
    }


def score_yield_spread_10y3m() -> dict:
    """
    Spread 10Y-3M — modelo preferido do Fed NY para previsão de recessão.
    Referência: Estrella & Mishkin (1998).
    """
    series = _load_series("YIELD_SPREAD_10Y3M")
    if series.empty:
        return {"prob": None, "current_value": None, "signal": "sem dados"}

    last = series.iloc[-1]
    prob = float(1 / (1 + np.exp(1.2 * last)) * 100)

    if last < -0.5:   signal = "Inversão severa — alto risco"
    elif last < 0:    signal = "Curva invertida"
    elif last < 1.0:  signal = "Achatamento — atenção"
    else:             signal = "Normal"

    return {
        "prob":          prob,
        "current_value": float(last),
        "last_date":     series.index[-1].strftime("%b/%Y"),
        "signal":        signal,
        "n_obs":         len(series),
    }


def score_sahm_rule() -> dict:
    """
    Regra de Sahm (Sahm, 2019):
    Recessão sinalizada quando a taxa de desemprego de 3 meses sobe
    0.5pp ou mais em relação ao mínimo dos 12 meses anteriores.
    Valor ≥ 0.5 → recessão em curso.
    Prob linear: 0 = 0%, 0.5 = 50%, ≥1.0 = 100%
    """
    series = _load_series("SAHM_RULE")
    if series.empty:
        return {"prob": None, "current_value": None, "signal": "sem dados"}

    last = series.iloc[-1]
    prob = float(min(last / 1.0, 1.0) * 100)

    if last >= 0.5:  signal = "⚠ Sahm Rule ativada — recessão provável"
    elif last >= 0.3: signal = "Atenção — próximo do threshold"
    else:             signal = "Normal"

    return {
        "prob":          prob,
        "current_value": float(last),
        "last_date":     series.index[-1].strftime("%b/%Y"),
        "signal":        signal,
        "threshold":     0.5,
        "n_obs":         len(series),
    }


def score_leading_index() -> dict:
    """
    Leading Economic Index (Conference Board via FRED: USSLIND).
    Declínio consecutivo de 3 meses → sinal de recessão.
    Score baseado em momentum de 6 meses.
    """
    series = _load_series("LEADING_INDEX")
    if len(series) < 6:
        return {"prob": None, "current_value": None, "signal": "sem dados"}

    mom_6m = series.iloc[-1] - series.iloc[-7] if len(series) >= 7 else 0
    # Momentum negativo → maior probabilidade
    prob = float(max(0, min(100, 50 - mom_6m * 15)))

    last = series.iloc[-1]
    if mom_6m < -1:    signal = "Declínio acelerado — risco elevado"
    elif mom_6m < 0:   signal = "Declínio — atenção"
    elif mom_6m < 0.5: signal = "Estagnação"
    else:              signal = "Expansão"

    return {
        "prob":          prob,
        "current_value": float(last),
        "momentum_6m":   float(mom_6m),
        "last_date":     series.index[-1].strftime("%b/%Y"),
        "signal":        signal,
        "n_obs":         len(series),
    }


def score_official_recession_prob() -> dict:
    """
    Probabilidade oficial de recessão — Fed NY (série RECPROUSM156N via FRED).
    Modelo probit baseado no spread 10Y-3M.
    Este é o modelo de referência — se disponível, usa diretamente.
    """
    series = _load_series("RECESSION_PROB")
    if series.empty:
        return {"prob": None, "current_value": None, "signal": "sem dados"}

    last = float(series.iloc[-1])

    if last >= 50:    signal = "Alta probabilidade — Fed NY"
    elif last >= 25:  signal = "Probabilidade moderada"
    elif last >= 10:  signal = "Risco baixo-moderado"
    else:             signal = "Baixo risco"

    return {
        "prob":          last,
        "current_value": last,
        "last_date":     series.index[-1].strftime("%b/%Y"),
        "signal":        signal,
        "n_obs":         len(series),
    }


COMPONENT_FUNCS = {
    "Spread 10Y-2Y":      (score_yield_spread_10y2y, 0.20),
    "Spread 10Y-3M":      (score_yield_spread_10y3m, 0.25),
    "Sahm Rule":          (score_sahm_rule,           0.25),
    "Leading Index":      (score_leading_index,       0.15),
    "Prob. Fed NY":       (score_official_recession_prob, 0.15),
}


def calculate_recession_monitor() -> dict:
    """
    Calcula o score composto de recessão (0-100).
    Componentes ausentes têm peso redistribuído.
    """
    results = {}
    for name, (func, weight) in COMPONENT_FUNCS.items():
        results[name] = {"data": func(), "weight": weight}

    available = {k: v for k, v in results.items() if v["data"]["prob"] is not None}

    if not available:
        return {
            "recession_score":  None,
            "classification":   "Indisponível",
            "completeness_pct": 0.0,
            "components":       results,
        }

    weight_sum = sum(v["weight"] for v in available.values())
    score = sum(
        v["data"]["prob"] * (v["weight"] / weight_sum)
        for v in available.values()
    )

    if score < 15:    classification = "🟢 Baixo"
    elif score < 35:  classification = "🟡 Moderado"
    elif score < 60:  classification = "🟠 Elevado"
    else:             classification = "🔴 Crítico"

    return {
        "recession_score":  score,
        "classification":   classification,
        "completeness_pct": weight_sum * 100,
        "components":       results,
    }


def run():
    print("Recession Monitor — EUA\n")
    result = calculate_recession_monitor()
    for name, comp in result["components"].items():
        prob = comp["data"]["prob"]
        sig  = comp["data"].get("signal", "—")
        print(f"  {name:20s}: {'%.1f%%' % prob if prob is not None else '—':8s}  {sig}")
    print(f"\nScore: {result['recession_score']:.1f if result['recession_score'] else '—'} "
          f"({result['classification']})")


if __name__ == "__main__":
    run() 