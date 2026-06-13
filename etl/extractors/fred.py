"""
etl/extractors/fred.py
Extractor de séries macroeconômicas dos EUA via FRED API.
Requer FRED_API_KEY no .env (gratuita: https://fredaccount.stlouisfed.org/apikeys)

Séries relevantes para o estudo:
- GDP        : PIB nominal (US$ bn)
- GDPC1      : PIB real (encadeado)
- CPIAUCSL   : CPI (inflação)
- UNRATE     : Taxa de desemprego
- FEDFUNDS   : Fed Funds Rate
- DTWEXBGS   : Índice cambial (USD trade-weighted)
"""

import os
import requests
import pandas as pd
from pathlib import Path
from datetime import date

import sys
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR  # noqa: E402

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

SERIES_OF_INTEREST = {
    "GDP": "pib_nominal_usd_bn",
    "GDPC1": "pib_real_chained",
    "CPIAUCSL": "cpi_inflacao",
    "UNRATE": "taxa_desemprego",
    "FEDFUNDS": "fed_funds_rate",
    "DTWEXBGS": "indice_cambial_usd",
}


def fetch_series(series_id: str, api_key: str,
                  start: str = "2015-01-01", end: str | None = None) -> pd.DataFrame:
    """Busca uma série do FRED e retorna DataFrame (date, value)."""
    if end is None:
        end = date.today().isoformat()

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
        "observation_end": end,
    }

    resp = requests.get(FRED_BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    df = pd.DataFrame(data["observations"])[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    # FRED usa "." para missing
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["series_id"] = series_id
    return df.dropna(subset=["value"])


def run(start: str = "2015-01-01"):
    """Extrai todas as séries de interesse e salva em data/raw/."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError(
            "FRED_API_KEY não definida. Configure no .env "
            "(obtenha gratuitamente em https://fredaccount.stlouisfed.org/apikeys)"
        )

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    frames = []
    for series_id, label in SERIES_OF_INTEREST.items():
        print(f"Baixando {series_id} ({label})...")
        df = fetch_series(series_id, api_key, start=start)
        df["indicator_label"] = label
        frames.append(df)

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"fred_macro_usa_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} ({len(result)} linhas)")
    return result


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run()
