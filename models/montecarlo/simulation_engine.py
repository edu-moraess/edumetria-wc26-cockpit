"""
models/montecarlo/simulation_engine.py
Motor de simulação Monte Carlo — projeta indicadores macro 2027-2035
usando distribuições históricas observadas (bootstrap paramétrico).

Metodologia:
- Para cada indicador, estima a distribuição histórica de variações
  anuais (média e desvio padrão da série real disponível no banco).
- Simula N_SIMULATIONS trajetórias independentes para o horizonte
  2027-2035 (9 anos), assumindo normalidade dos incrementos anuais
  (simplificação documentada — para fat tails, EVT seria necessário).
- Retorna percentis P5/P25/P50/P75/P95 para cada ano.

LIMITAÇÕES EXPLÍCITAS:
- Assume normalidade (ignora fat tails e regimes)
- Ignora correlação entre indicadores e países
- Projeções condicionadas ao padrão histórico observado — choques
  futuros (Copa 2026, geopolítica) não estão modelados como shocks
  exógenos nesta versão (fase pós-MVP)
- N_SIMULATIONS reduzido para ambiente Streamlit (10k-50k)
  para evitar timeout

Uso:
    python -m models.montecarlo.simulation_engine
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import (  # noqa: E402
    MONTE_CARLO_RANDOM_SEED,
    FORECAST_START_YEAR,
    FORECAST_END_YEAR,
)
from database.connection import get_connection  # noqa: E402

N_SIMULATIONS = 20_000   # balanceia precisão e performance no Streamlit Cloud
FORECAST_YEARS = list(range(FORECAST_START_YEAR, FORECAST_END_YEAR + 1))
N_YEARS = len(FORECAST_YEARS)


def _load_annual_series(indicator_code: str, country_code: str) -> pd.Series:
    """Carrega série anual de um indicador do banco."""
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
    return series.dropna()


def run_simulation(
    indicator_code: str,
    country_code: str,
    n_simulations: int = N_SIMULATIONS,
    seed: int = MONTE_CARLO_RANDOM_SEED,
) -> dict | None:
    """
    Executa simulação Monte Carlo para um indicador/país.
    Retorna dict com percentis por ano, ou None se dados insuficientes.
    """
    series = _load_annual_series(indicator_code, country_code)

    if len(series) < 5:
        return None

    # Calcula variações anuais (retornos)
    annual_changes = series.pct_change().dropna()

    if len(annual_changes) < 3:
        return None

    mu = float(annual_changes.mean())
    sigma = float(annual_changes.std())
    last_value = float(series.iloc[-1])

    # Simula trajetórias
    rng = np.random.default_rng(seed)
    shocks = rng.normal(loc=mu, scale=sigma, size=(n_simulations, N_YEARS))
    paths = np.zeros((n_simulations, N_YEARS))

    for t in range(N_YEARS):
        if t == 0:
            paths[:, t] = last_value * (1 + shocks[:, t])
        else:
            paths[:, t] = paths[:, t - 1] * (1 + shocks[:, t])

    # Percentis por ano
    percentiles = {}
    for i, year in enumerate(FORECAST_YEARS):
        col = paths[:, i]
        percentiles[year] = {
            "p05": float(np.percentile(col, 5)),
            "p25": float(np.percentile(col, 25)),
            "p50": float(np.percentile(col, 50)),
            "p75": float(np.percentile(col, 75)),
            "p95": float(np.percentile(col, 95)),
            "mean": float(np.mean(col)),
        }

    return {
        "indicator_code": indicator_code,
        "country_code": country_code,
        "n_simulations": n_simulations,
        "mu": mu,
        "sigma": sigma,
        "last_observed_value": last_value,
        "last_observed_year": int(series.index[-1].year),
        "forecast_years": FORECAST_YEARS,
        "percentiles": percentiles,
    }


def run():
    indicators = [
        ("GDP_NOMINAL", "USA"),
        ("GDP_REAL", "USA"),
        ("CPI", "USA"),
        ("UNEMPLOYMENT_RATE", "USA"),
        ("TOURISM_ARRIVALS", "CAN"),
        ("TOURISM_ARRIVALS", "MEX"),
    ]

    for code, country in indicators:
        print(f"\n--- {code} ({country}) ---")
        result = run_simulation(code, country)
        if result is None:
            print("  Dados insuficientes.")
            continue
        print(f"  Obs: {result['last_observed_year']} · Último: {result['last_observed_value']:,.2f}")
        print(f"  μ anual: {result['mu']*100:.2f}% · σ: {result['sigma']*100:.2f}%")
        p = result["percentiles"][FORECAST_YEARS[-1]]
        print(f"  2035 P50: {p['p50']:,.2f} · P05: {p['p05']:,.2f} · P95: {p['p95']:,.2f}")


if __name__ == "__main__":
    run()