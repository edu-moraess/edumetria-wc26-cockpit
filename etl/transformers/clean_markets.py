"""
etl/transformers/clean_markets.py
Normaliza dados de mercado do yfinance (data/raw/yfinance_markets_*.csv)
para o formato "tidy" que alimenta fact_indicator_values.

Saída: data/processed/markets.parquet
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR  # noqa: E402

# Mapeia label do yfinance -> (indicator_code, country_code ou None p/ global)
INDICATOR_MAP = {
    "sp500_usa": ("SP500", "USA"),
    "tsx_canada": ("TSX", "CAN"),
    "ipc_mexico": ("IPC_MEXICO", "MEX"),
    "vix": ("VIX", None),
    "wti_crude": ("WTI_CRUDE", None),
    "brent_crude": ("BRENT_CRUDE", None),
    "etf_aviacao": ("ETF_AVIATION", None),
    "etf_lazer_entretenimento": ("ETF_LEISURE", None),
    "consumo_discricionario_usa": ("ETF_CONSUMER_DISCRETIONARY", "USA"),
}


def find_latest_raw_file() -> Path:
    files = sorted(RAW_DATA_DIR.glob("yfinance_markets_*.csv"))
    if not files:
        raise FileNotFoundError(
            "Nenhum arquivo yfinance_markets_*.csv encontrado em data/raw/. "
            "Rode: python -m etl.extractors.yfinance_markets"
        )
    return files[-1]


def run(input_path: Path | None = None) -> pd.DataFrame:
    if input_path is None:
        input_path = find_latest_raw_file()

    print(f"Lendo {input_path}...")
    df = pd.read_csv(input_path, parse_dates=["date"])

    rows = []
    for label, (indicator_code, country_code) in INDICATOR_MAP.items():
        subset = df[df["indicator_label"] == label]
        if subset.empty:
            continue
        rows.append(pd.DataFrame({
            "country_code": country_code,  # None = indicador global
            "indicator_code": indicator_code,
            "period": subset["date"],
            "period_type": "daily",
            "value": subset["close"],
            "source_name": "yfinance",
            "is_forecast": False,
        }))

    out = pd.concat(rows, ignore_index=True)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DATA_DIR / "markets.parquet"
    out.to_parquet(out_path, index=False)
    print(f"Salvo: {out_path} ({len(out)} linhas)")
    return out


if __name__ == "__main__":
    run()
