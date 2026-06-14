"""
models/montecarlo/simulation_engine.py
Monte Carlo 2.0 — Bootstrap com distribuição Student-t (fat tails).

METODOLOGIA:
  Versão 1.0: bootstrap paramétrico com distribuição normal (μ, σ).
  Versão 2.0: distribuição Student-t (μ, σ, ν) onde ν = graus de
  liberdade estimados por Maximum Likelihood sobre os retornos históricos.
  Student-t com ν baixo (3-8) captura fat tails observados em séries
  econômicas — superior à normal para stress testing.

  Fallback automático: se MLE falhar, usa distribuição normal (v1.0).

LIMITAÇÕES:
  - Assume IID dos retornos (ignora autocorrelação e GARCH)
  - Não modela regime switching (estabilidade vs. crise)
  - Não captura correlação entre indicadores e países
  - Stress testing com choques exógenos: fase pós-MVP

REFERÊNCIA:
  McNeil, A.J., Frey, R. & Embrechts, P. (2015). "Quantitative Risk
  Management." Princeton University Press. Cap. 3 (distribuições
  de caudas pesadas em finanças).

Uso:
    python -m models.montecarlo.simulation_engine
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import (  # noqa: E402
    MONTE_CARLO_RANDOM_SEED,
    FORECAST_START_YEAR,
    FORECAST_END_YEAR,
)
from database.connection import get_connection  # noqa: E402

N_SIMULATIONS  = 20_000
FORECAST_YEARS = list(range(FORECAST_START_YEAR, FORECAST_END_YEAR + 1))
N_YEARS        = len(FORECAST_YEARS)


def _load_annual_series(indicator_code: str, country_code: str) -> pd.Series:
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
    series = df.set_index("period")["value"].resample("YE").last()
    if len(series) > 1:
        median = series.median()
        series = series[series > median * 0.5]
    return series.dropna()


def _fit_student_t(changes: pd.Series) -> tuple[float, float, float]:
    """
    Ajusta distribuição Student-t via MLE.
    Retorna (df, loc, scale).
    Fallback: (30, mean, std) ≈ normal se MLE falhar.
    """
    try:
        df_t, loc, scale = stats.t.fit(changes)
        df_t = max(2.1, min(df_t, 30))  # clip: 2.1 (fat tails) a 30 (≈ normal)
        return df_t, loc, scale
    except Exception:
        return 30.0, float(changes.mean()), float(changes.std())


def run_simulation(
    indicator_code: str,
    country_code:   str,
    n_simulations:  int   = N_SIMULATIONS,
    seed:           int   = MONTE_CARLO_RANDOM_SEED,
    use_student_t:  bool  = True,
) -> dict | None:
    """
    Executa simulação Monte Carlo 2.0.
    use_student_t=True: distribuição Student-t (fat tails)
    use_student_t=False: distribuição normal (v1.0, fallback)
    """
    series = _load_annual_series(indicator_code, country_code)

    if len(series) < 5:
        return None

    annual_changes = series.pct_change().dropna()

    if len(annual_changes) < 3:
        return None

    last_value = float(series.iloc[-1])
    rng        = np.random.default_rng(seed)

    # --- Fit da distribuição ---
    if use_student_t and len(annual_changes) >= 5:
        df_t, loc, scale = _fit_student_t(annual_changes)
        distribution     = "student-t"
        shocks = rng.standard_t(df=df_t, size=(n_simulations, N_YEARS)) * scale + loc
    else:
        mu, sigma    = float(annual_changes.mean()), float(annual_changes.std())
        df_t         = 30.0
        loc, scale   = mu, sigma
        distribution = "normal"
        shocks = rng.normal(loc=mu, scale=sigma, size=(n_simulations, N_YEARS))

    # --- Simula trajetórias ---
    paths = np.zeros((n_simulations, N_YEARS))
    for t in range(N_YEARS):
        if t == 0:
            paths[:, t] = last_value * (1 + shocks[:, t])
        else:
            paths[:, t] = paths[:, t - 1] * (1 + shocks[:, t])

    # --- Percentis ---
    percentiles = {}
    for i, year in enumerate(FORECAST_YEARS):
        col = paths[:, i]
        percentiles[year] = {
            "p05":  float(np.percentile(col, 5)),
            "p25":  float(np.percentile(col, 25)),
            "p50":  float(np.percentile(col, 50)),
            "p75":  float(np.percentile(col, 75)),
            "p95":  float(np.percentile(col, 95)),
            "mean": float(np.mean(col)),
        }

    return {
        "indicator_code":      indicator_code,
        "country_code":        country_code,
        "n_simulations":       n_simulations,
        "distribution":        distribution,
        "df_t":                df_t,
        "loc":                 loc,
        "scale":               scale,
        "mu":                  loc,      # compatibilidade com v1.0
        "sigma":               scale,    # compatibilidade com v1.0
        "last_observed_value": last_value,
        "last_observed_year":  int(series.index[-1].year),
        "forecast_years":      FORECAST_YEARS,
        "percentiles":         percentiles,
    }


def run():
    indicators = [
        ("GDP_NOMINAL",      "USA"),
        ("GDP_REAL",         "USA"),
        ("CPI",              "USA"),
        ("UNEMPLOYMENT_RATE","USA"),
        ("TOURISM_ARRIVALS", "CAN"),
        ("TOURISM_ARRIVALS", "MEX"),
    ]
    for code, country in indicators:
        print(f"\n--- {code} ({country}) ---")
        result = run_simulation(code, country)
        if result is None:
            print("  Dados insuficientes.")
            continue
        dist = result["distribution"]
        df_t = result["df_t"]
        print(f"  Distribuição: {dist} (ν={df_t:.1f})")
        print(f"  Último: {result['last_observed_value']:,.2f} ({result['last_observed_year']})")
        p = result["percentiles"][FORECAST_YEARS[-1]]
        print(f"  2035 P50: {p['p50']:,.2f} · P05: {p['p05']:,.2f} · P95: {p['p95']:,.2f}")


if __name__ == "__main__":
    run()