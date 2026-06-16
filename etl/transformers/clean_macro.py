"""
etl/transformers/clean_macro.py
Normaliza dados macro do FRED para o formato tidy.
Calcula YIELD_SPREAD_10Y2Y = GS10 - GS2 (indicador derivado).
"""

import sys
from pathlib import Path
from datetime import date

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR  # noqa: E402

INDICATOR_MAP = {
    "pib_nominal_usd_bn":  "GDP_NOMINAL",
    "pib_real_chained":    "GDP_REAL",
    "cpi_inflacao":        "CPI",
    "taxa_desemprego":     "UNEMPLOYMENT_RATE",
    "fed_funds_rate":      "POLICY_RATE",
    "indice_cambial_usd":  "FX_INDEX",
    "treasury_10y":        "TREASURY_10Y",
    "treasury_2y":         "TREASURY_2Y",
}


def find_latest_raw_file() -> Path:
    files = sorted(RAW_DATA_DIR.glob("fred_macro_usa_*.csv"))
    if not files:
        raise FileNotFoundError(
            "Nenhum arquivo fred_macro_usa_*.csv em data/raw/. "
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
        "country_code":  "USA",
        "indicator_code": df["indicator_code"],
        "period":         df["date"],
        "period_type":    "monthly",
        "value":          df["value"],
        "source_name":    "FRED",
        "is_forecast":    False,
    })

    # --- Calcula Yield Spread 10Y-2Y (indicador derivado) ---
    t10 = out[out["indicator_code"] == "TREASURY_10Y"].set_index("period")["value"]
    t2  = out[out["indicator_code"] == "TREASURY_2Y"].set_index("period")["value"]

    if not t10.empty and not t2.empty:
        spread = (t10 - t2).dropna().reset_index()
        spread.columns = ["period", "value"]
        spread["country_code"]   = "USA"
        spread["indicator_code"] = "YIELD_SPREAD_10Y2Y"
        spread["period_type"]    = "monthly"
        spread["source_name"]    = "FRED"
        spread["is_forecast"]    = False
        out = pd.concat([out, spread], ignore_index=True)
        print(f"  → Yield Spread 10Y-2Y calculado: {len(spread)} observações.")

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DATA_DIR / "macro_usa.parquet"
    out.to_parquet(out_path, index=False)
    print(f"Salvo: {out_path} ({len(out)} linhas)")
    return out


if __name__ == "__main__":
    run()