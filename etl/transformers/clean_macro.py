"""
etl/transformers/clean_macro.py
Normaliza dados macro do FRED (data/raw/fred_macro_usa_*.csv) para o
formato "tidy" que alimenta fact_indicator_values.

Saída: data/processed/macro_usa.parquet
Colunas: country_code, indicator_code, period, period_type, value,
         source_name, is_forecast
"""

import sys
from pathlib import Path
from datetime import date

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR  # noqa: E402

# Mapeia label do FRED -> indicator_code do dim_indicator
INDICATOR_MAP = {
    "pib_nominal_usd_bn": "GDP_NOMINAL",
    "pib_real_chained": "GDP_REAL",
    "cpi_inflacao": "CPI",
    "taxa_desemprego": "UNEMPLOYMENT_RATE",
    "fed_funds_rate": "POLICY_RATE",
    "indice_cambial_usd": "FX_INDEX",
}


def find_latest_raw_file() -> Path:
    files = sorted(RAW_DATA_DIR.glob("fred_macro_usa_*.csv"))
    if not files:
        raise FileNotFoundError(
            "Nenhum arquivo fred_macro_usa_*.csv encontrado em data/raw/. "
            "Rode: python -m etl.extractors.fred"
        )
    return files[-1]


def run(input_path: Path | None = None) -> pd.DataFrame:
    if input_path is None:
        input_path = find_latest_raw_file()

    print(f"Lendo {input_path}...")
    df = pd.read_csv(input_path, parse_dates=["date"])

    df["indicator_code"] = df["indicator_label"].map(INDICATOR_MAP)
    df = df.dropna(subset=["indicator_code"])

    out = pd.DataFrame({
        "country_code": "USA",
        "indicator_code": df["indicator_code"],
        "period": df["date"],
        "period_type": "monthly",
        "value": df["value"],
        "source_name": "FRED",
        "is_forecast": False,
    })

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DATA_DIR / "macro_usa.parquet"
    out.to_parquet(out_path, index=False)
    print(f"Salvo: {out_path} ({len(out)} linhas)")
    return out


if __name__ == "__main__":
    run()
