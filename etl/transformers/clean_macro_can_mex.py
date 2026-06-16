"""
etl/transformers/clean_macro_can_mex.py
Normaliza dados macro do Canadá (StatCan) e México (INEGI) para o
formato tidy — mesmo padrão do clean_macro.py (EUA/FRED).
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR  # noqa: E402

INDICATOR_MAP = {
    "GDP_REAL_CAN": "GDP_REAL",
    "CPI_CAN": "CPI",
    "UNEMPLOYMENT_RATE_CAN": "UNEMPLOYMENT_RATE",
    "POLICY_RATE_CAN": "POLICY_RATE",
    "GDP_REAL_MEX": "GDP_REAL",
    "CPI_MEX": "CPI",
    "UNEMPLOYMENT_RATE_MEX": "UNEMPLOYMENT_RATE",
}

SOURCE_MAP = {
    "CAN": "StatCan",
    "MEX": "INEGI",
}


def run():
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    frames = []

    # Canadá
    can_files = sorted(RAW_DATA_DIR.glob("statcan_macro_can_*.csv"))
    if can_files:
        df = pd.read_csv(can_files[-1], parse_dates=["date"])
        df["country"] = "CAN"
        frames.append(df)
    else:
        print("⚠️  Nenhum arquivo statcan_macro_can_*.csv — rode o extractor primeiro.")

    # México
    mex_files = sorted(RAW_DATA_DIR.glob("inegi_macro_mex_*.csv"))
    if mex_files:
        df = pd.read_csv(mex_files[-1], parse_dates=["date"])
        df["country"] = "MEX"
        frames.append(df)
    else:
        print("⚠️  Nenhum arquivo inegi_macro_mex_*.csv — rode o extractor primeiro.")

    if not frames:
        return None

    df = pd.concat(frames, ignore_index=True)
    df["indicator_code"] = df["indicator_label"].map(INDICATOR_MAP)
    df = df.dropna(subset=["indicator_code"])

    out = pd.DataFrame({
        "country_code": df["country"],
        "indicator_code": df["indicator_code"],
        "period": df["date"],
        "period_type": "quarterly",
        "value": df["value"],
        "source_name": df["country"].map(SOURCE_MAP),
        "is_forecast": False,
    })

    out_path = PROCESSED_DATA_DIR / "macro_can_mex.parquet"
    out.to_parquet(out_path, index=False)
    print(f"Salvo: {out_path} ({len(out)} linhas)")
    return out


if __name__ == "__main__":
    run() 