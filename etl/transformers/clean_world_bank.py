"""
etl/transformers/clean_world_bank.py
Transforma dados brutos do World Bank para formato tidy (fact_indicator_values).

Entrada: data/raw/world_bank_YYYY-MM-DD.csv
Saída: data/processed/world_bank.parquet
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR  # noqa: E402


def find_latest_raw_file() -> Path:
    files = sorted(RAW_DATA_DIR.glob("world_bank_*.csv"))
    if not files:
        raise FileNotFoundError(
            "Nenhum arquivo world_bank_*.csv em data/raw/. "
            "Rode: python -m etl.extractors.world_bank"
        )
    return files[-1]


def run(input_path: Path = None) -> pd.DataFrame:
    if input_path is None:
        input_path = find_latest_raw_file()

    print(f"Lendo {input_path}...")
    df = pd.read_csv(input_path, parse_dates=["date"])

    # Formato tidy já está quase pronto, só padronizar
    out = pd.DataFrame({
        "country_code": df["country_code"],
        "indicator_code": df["indicator_code"],
        "period": df["date"],
        "period_type": "yearly",
        "value": df["value"],
        "source_name": "WorldBank",
        "is_forecast": False,
    })

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DATA_DIR / "world_bank.parquet"
    out.to_parquet(out_path, index=False)
    print(f"Salvo: {out_path} ({len(out)} linhas)")
    return out


if __name__ == "__main__":
    run()
