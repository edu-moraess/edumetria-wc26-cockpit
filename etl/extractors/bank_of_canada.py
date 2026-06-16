"""
etl/extractors/bank_of_canada.py
Extractor de dados macroeconômicos do Canadá via Bank of Canada Valet API.
API pública, sem autenticação necessária.

REFERÊNCIA: https://www.bankofcanada.ca/valet/docs
"""

import sys
from pathlib import Path
from datetime import date

import requests
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR  # noqa: E402

BOC_BASE_URL = "https://www.bankofcanada.ca/valet"

# Séries relevantes do Bank of Canada
BOC_SERIES = {
    "V39079":    "policy_rate_canada",          # overnight rate
    "V41690973": "cpi_canada",                   # CPI total
    "V2064705":  "unemployment_rate_canada",
    "V37426":    "exchange_rate_cad_usd",        # CAD/USD
    "V123530":   "gdp_real_canada_quarterly",
}

START_DATE = "2010-01-01"


def fetch_boc_series(series_name: str) -> pd.DataFrame:
    url    = f"{BOC_BASE_URL}/series/{series_name}/observations"
    params = {"start_date": START_DATE, "end_date": date.today().isoformat()}
    resp   = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data   = resp.json()

    obs = data.get("observations", [])
    if not obs:
        return pd.DataFrame()

    rows = []
    for item in obs:
        val = item.get(series_name, {}).get("v")
        if val is not None:
            try:
                rows.append({"date": item["d"], "value": float(val)})
            except (ValueError, TypeError):
                pass

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today  = date.today().isoformat()
    frames = []

    for series_name, label in BOC_SERIES.items():
        print(f"Baixando Bank of Canada {series_name} ({label})...")
        try:
            df = fetch_boc_series(series_name)
            if df.empty:
                print(f"  ⚠️  Sem dados para {series_name}")
                continue
            df["indicator_label"] = label
            df["country"]         = "CAN"
            frames.append(df)
            print(f"  → {len(df)} observações")
        except Exception as e:
            print(f"  ⚠️  Erro {series_name}: {e}")

    if not frames:
        print("Nenhum dado extraído do Bank of Canada.")
        return None

    result   = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"bank_of_canada_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\nSalvo: {out_path} ({len(result):,} linhas)")
    return result


if __name__ == "__main__":
    run() 