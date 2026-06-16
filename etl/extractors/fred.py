"""
etl/extractors/fred.py
Extractor de séries macroeconômicas dos EUA via FRED API.
Requer FRED_API_KEY no Streamlit Cloud Secrets ou .env local.
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

SERIES_OF_INTEREST = {
    "GDP":       "pib_nominal_usd_bn",
    "GDPC1":     "pib_real_chained",
    "CPIAUCSL":  "cpi_inflacao",
    "UNRATE":    "taxa_desemprego",
    "FEDFUNDS":  "fed_funds_rate",
    "DTWEXBGS":  "indice_cambial_usd",
    "GS10":      "treasury_10y",       # Treasury 10 anos — NOVO
    "GS2":       "treasury_2y",        # Treasury 2 anos — NOVO
}


def fetch_series(series_id: str, api_key: str,
                 start: str = "2015-01-01", end: str | None = None) -> pd.DataFrame:
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
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["series_id"] = series_id
    return df.dropna(subset=["value"])


def run(start: str = "2015-01-01"):
    api_key = get_secret("FRED_API_KEY")
    if not api_key:
        raise RuntimeError(
            "FRED_API_KEY não definida. Configure nos Secrets do Streamlit Cloud "
            "ou no .env local. Obter em: https://fredaccount.stlouisfed.org/apikeys"
        )

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    for series_id, label in SERIES_OF_INTEREST.items():
        print(f"Baixando {series_id} ({label})...")
        try:
            df = fetch_series(series_id, api_key, start=start)
            df["indicator_label"] = label
            frames.append(df)
        except Exception as e:
            print(f"  ⚠️  Erro em {series_id}: {e}")

    if not frames:
        print("Nenhum dado extraído do FRED.")
        return None

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"fred_macro_usa_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} ({len(result)} linhas)")
    return result


if __name__ == "__main__":
    run() 