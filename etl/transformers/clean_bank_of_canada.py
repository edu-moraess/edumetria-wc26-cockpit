"""
etl/transformers/clean_bank_of_canada.py
Normaliza dados do Bank of Canada para formato tidy.
Substitui/complementa o StatCan macro para dados macroeconômicos do Canadá.
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR  # noqa: E402

INDICATOR_MAP = {
    "policy_rate_canada":        "POLICY_RATE",
    "cpi_canada":                "CPI",
    "unemployment_rate_canada":  "UNEMPLOYMENT_RATE",
    "exchange_rate_cad_usd":     "FX_CAD_USD",
    "gdp_real_canada_quarterly": "GDP_REAL",
}

PERIOD_TYPE_MAP = {
    "policy_rate_canada":        "daily",
    "cpi_canada":                "monthly",
    "unemployment_rate_canada":  "monthly",
    "exchange_rate_cad_usd":     "daily",
    "gdp_real_canada_quarterly": "quarterly",
}


def find_latest() -> Path | None:
    files = sorted(RAW_DATA_DIR.glob("bank_of_canada_*.csv"))
    return files[-1] if files else None


def run() -> pd.DataFrame | None:
    path = find_latest()
    if not path:
        print("⚠️  bank_of_canada_*.csv não encontrado — rode o extractor primeiro.")
        return None

    print(f"Lendo {path.name}...")
    df = pd.read_csv(path, parse_dates=["date"])
    df["indicator_code"] = df["indicator_label"].map(INDICATOR_MAP)
    df["period_type"]    = df["indicator_label"].map(PERIOD_TYPE_MAP)
    df = df.dropna(subset=["indicator_code", "value"])

    out = pd.DataFrame({
        "country_code":   "CAN",
        "indicator_code": df["indicator_code"],
        "period":         df["date"],
        "period_type":    df["period_type"],
        "value":          df["value"],
        "source_name":    "BoC",
        "is_forecast":    False,
    })

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DATA_DIR / "macro_can_boc.parquet"
    out.to_parquet(out_path, index=False)
    print(f"Salvo: {out_path} ({len(out):,} linhas)")
    return out


if __name__ == "__main__":
    run()