"""
etl/transformers/clean_tourism.py
Normaliza dados de turismo (StatCan/Banxico) de
data/raw/tourism_open_sources_*.csv para o formato "tidy".

Saída: data/processed/tourism.parquet
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR  # noqa: E402

INDICATOR_MAP = {
    "chegadas_internacionais_canada_total": "TOURISM_ARRIVALS",
    "turistas_internacionais_mexico": "TOURISM_ARRIVALS",
}


def find_latest_raw_file() -> Path:
    files = sorted(RAW_DATA_DIR.glob("tourism_open_sources_*.csv"))
    if not files:
        raise FileNotFoundError(
            "Nenhum arquivo tourism_open_sources_*.csv encontrado em data/raw/. "
            "Rode: python -m etl.extractors.tourism_open_sources"
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
        "country_code": df["country"],
        "indicator_code": df["indicator_code"],
        "period": df["date"],
        "period_type": "monthly",
        "value": df["value"],
        "source_name": df["country"].map({"CAN": "StatCan", "MEX": "Banxico"}),
        "is_forecast": False,
    })

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DATA_DIR / "tourism.parquet"
    out.to_parquet(out_path, index=False)
    print(f"Salvo: {out_path} ({len(out)} linhas)")
    return out


if __name__ == "__main__":
    run()