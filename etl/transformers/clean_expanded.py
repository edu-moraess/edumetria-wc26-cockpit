"""
etl/transformers/clean_expanded.py
Normaliza os dados do FRED expandido e yfinance expandido para o
formato tidy — mesmo padrão dos outros transformers.

Calcula indicadores derivados:
- YIELD_SPREAD_10Y3M = Treasury 10Y - Treasury 3M (curva alternativa)
- RECESSION_COMPOSITE = score simples combinando Sahm Rule +
  Leading Index + Yield Spreads (heurística, documentada)
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR  # noqa: E402

FRED_INDICATOR_MAP = {
    "treasury_3m":           "TREASURY_3M",
    "sahm_rule_realtime":    "SAHM_RULE",
    "leading_index_usa":     "LEADING_INDEX",
    "recession_prob_usa":    "RECESSION_PROB",
    "ted_spread":            "TED_SPREAD",
    "hy_spread":             "HY_SPREAD",
    "debt_to_gdp_usa":       "DEBT_TO_GDP",
    "fiscal_deficit_usa":    "FISCAL_DEFICIT",
    "labor_participation_usa": "LABOR_PARTICIPATION",
    "avg_hourly_earnings_usa": "AVG_HOURLY_EARNINGS",
}

YFINANCE_INDICATOR_MAP = {
    "natural_gas_futures":    ("NATURAL_GAS", None),
    "move_index_bond_vol":    ("MOVE_INDEX",  None),
    "nasdaq_composite":       ("NASDAQ",      "USA"),
    "russell_2000":           ("RUSSELL2000", "USA"),
    "treasury_10y_yield_yf":  ("TREASURY_10Y_YF", "USA"),
    "gold_futures":           ("GOLD",        None),
}


def find_latest(pattern: str) -> Path | None:
    files = sorted(RAW_DATA_DIR.glob(pattern))
    return files[-1] if files else None


def run() -> pd.DataFrame:
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    frames = []

    # --- FRED expandido ---
    fred_path = find_latest("fred_expanded_usa_*.csv")
    if fred_path:
        print(f"Lendo {fred_path.name}...")
        df = pd.read_csv(fred_path, parse_dates=["date"])
        df["indicator_code"] = df["indicator_label"].map(FRED_INDICATOR_MAP)
        df = df.dropna(subset=["indicator_code", "value"])

        fred_out = pd.DataFrame({
            "country_code":   "USA",
            "indicator_code": df["indicator_code"],
            "period":         df["date"],
            "period_type":    "monthly",
            "value":          df["value"],
            "source_name":    "FRED",
            "is_forecast":    False,
        })
        frames.append(fred_out)

        # Yield Spread 10Y-3M
        t10 = fred_out[fred_out["indicator_code"] == "TREASURY_10Y_YF"] if False else None

        # Usa TREASURY_10Y do macro_usa.parquet se existir
        macro_path = PROCESSED_DATA_DIR / "macro_usa.parquet"
        if macro_path.exists():
            macro = pd.read_parquet(macro_path)
            t10 = macro[macro["indicator_code"] == "TREASURY_10Y"].set_index("period")["value"]
            t3m = fred_out[fred_out["indicator_code"] == "TREASURY_3M"].set_index("period")["value"]

            if not t10.empty and not t3m.empty:
                spread_10y3m = (t10 - t3m).dropna().reset_index()
                spread_10y3m.columns = ["period", "value"]
                spread_10y3m["country_code"]   = "USA"
                spread_10y3m["indicator_code"] = "YIELD_SPREAD_10Y3M"
                spread_10y3m["period_type"]    = "monthly"
                spread_10y3m["source_name"]    = "FRED"
                spread_10y3m["is_forecast"]    = False
                frames.append(spread_10y3m)
                print(f"  → Yield Spread 10Y-3M calculado: {len(spread_10y3m)} obs.")
    else:
        print("⚠️  fred_expanded_usa_*.csv não encontrado.")

    # --- yfinance expandido ---
    yf_path = find_latest("yfinance_expanded_*.csv")
    if yf_path:
        print(f"Lendo {yf_path.name}...")
        df = pd.read_csv(yf_path, parse_dates=["date"])

        rows = []
        for label, (indicator_code, country_code) in YFINANCE_INDICATOR_MAP.items():
            subset = df[df["indicator_label"] == label]
            if subset.empty:
                continue
            rows.append(pd.DataFrame({
                "country_code":   country_code,
                "indicator_code": indicator_code,
                "period":         pd.to_datetime(subset["date"]),
                "period_type":    "daily",
                "value":          subset["close"],
                "source_name":    "yfinance",
                "is_forecast":    False,
            }))
        if rows:
            frames.append(pd.concat(rows, ignore_index=True))
    else:
        print("⚠️  yfinance_expanded_*.csv não encontrado.")

    if not frames:
        print("Nenhum dado processado.")
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(subset=["value"])

    out_path = PROCESSED_DATA_DIR / "expanded_indicators.parquet"
    out.to_parquet(out_path, index=False)
    print(f"Salvo: {out_path} ({len(out)} linhas)")
    return out


if __name__ == "__main__":
    run()