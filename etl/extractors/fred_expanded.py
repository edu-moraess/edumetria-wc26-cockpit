"""
etl/extractors/fred_expanded.py
Extractor expandido — séries adicionais do FRED para:
- Recession Monitor (Sahm Rule, Leading Indicators, Treasury 10Y-3M)
- Risk Score 2.0 (Natural Gas via yfinance, MOVE proxy)
- Economic Surprise (base para futuras comparações)

Todas as séries são gratuitas via FRED API.
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import date

import sys
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR  # noqa: E402
from config_secrets import get_secret  # noqa: E402

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Séries expandidas — Risk Score 2.0 + Recession Monitor
SERIES_EXPANDED = {
    # Yield curve adicional
    "GS3M":         "treasury_3m",
    # Recession Monitor
    "SAHMREALTIME": "sahm_rule_realtime",
    "USSLIND":      "leading_index_usa",
    "RECPROUSM156N":"recession_prob_usa",
    # Crédito / stress financeiro
    "TEDRATE":      "ted_spread",
    "BAMLH0A0HYM2": "hy_spread",
    # Fiscal / soberania
    "GFDEGDQ188S":  "debt_to_gdp_usa",
    "FYFSGDA188S":  "fiscal_deficit_usa",
    # Mercado de trabalho
    "CIVPART":      "labor_participation_usa",
    "AHETPI":       "avg_hourly_earnings_usa",
}


def fetch_series(series_id: str, api_key: str,
                 start: str = "2015-01-01", end: str | None = None) -> pd.DataFrame:
    if end is None:
        end = date.today().isoformat()

    params = {
        "series_id":         series_id,
        "api_key":           api_key,
        "file_type":         "json",
        "observation_start": start,
        "observation_end":   end,
    }

    resp = requests.get(FRED_BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    df = pd.DataFrame(data["observations"])[["date", "value"]]
    df["date"]  = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["series_id"] = series_id
    return df.dropna(subset=["value"])


def run(start: str = "2010-01-01"):
    api_key = get_secret("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("FRED_API_KEY não definida.")

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today  = date.today().isoformat()
    frames = []

    for series_id, label in SERIES_EXPANDED.items():
        print(f"Baixando {series_id} ({label})...")
        try:
            df = fetch_series(series_id, api_key, start=start)
            df["indicator_label"] = label
            frames.append(df)
        except Exception as e:
            print(f"  ⚠️  Erro em {series_id}: {e}")

    if not frames:
        print("Nenhum dado extraído.")
        return None

    result  = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"fred_expanded_usa_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} ({len(result)} linhas)")
    return result


if __name__ == "__main__":
    run()