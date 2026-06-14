"""
etl/transformers/clean_expanded.py
Normaliza dados expandidos (FRED + yfinance expandido) para formato tidy.

CORREÇÕES v2:
- SOFR substitui TED Spread (descontinuado)
- MOVE Index via FRED (BAMLMOVE1WMPIM156) substitui ^MOVE (yfinance instável)
- Yield Spread 10Y-3M calculado corretamente
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
    "treasury_3m":              "TREASURY_3M",
    "sahm_rule_realtime":       "SAHM_RULE",
    "leading_index_usa":        "LEADING_INDEX",
    "recession_prob_usa":       "RECESSION_PROB",
    "sofr_rate":                "SOFR_RATE",
    "hy_spread":                "HY_SPREAD",
    "move_index_fred":          "MOVE_INDEX",
    "debt_to_gdp_usa":          "DEBT_TO_GDP",
    "fiscal_deficit_usa":       "FISCAL_DEFICIT",
    "labor_participation_usa":  "LABOR_PARTICIPATION",
    "avg_hourly_earnings_usa":  "AVG_HOURLY_EARNINGS",
    "consumer_sentiment_umich": "CONSUMER_SENTIMENT",
    "retail_sales_usa":         "RETAIL_SALES",
}

YFINANCE_INDICATOR_MAP = {
    "natural_gas_futures":   ("NATURAL_GAS",      None),
    "nasdaq_composite":      ("NASDAQ",            "USA"),
    "russell_2000":          ("RUSSELL2000",       "USA"),
    "gold_futures":          ("GOLD",              None),
    "treasury_10y_yield_yf": ("TREASURY_10Y_YF",  "USA"),
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
        print(f"  → {len(fred_out)} linhas FRED expandido")

        # Yield Spread 10Y-3M derivado
        macro_path = PROCESSED_DATA_DIR / "macro_usa.parquet"
        if macro_path.exists():
            macro = pd.read_parquet(macro_path)
            t10 = macro[macro["indicator_code"] == "TREASURY_10Y"].set_index("period")["value"]
            t3m = fred_out[fred_out["indicator_code"] == "TREASURY_3M"].set_index("period")["value"]

            if not t10.empty and not t3m.empty:
                # Alinha no mesmo índice mensal
                t10_m = t10.resample("MS").last()
                t3m_m = t3m.resample("MS").last()
                spread = (t10_m - t3m_m).dropna().reset_index()
                spread.columns = ["period", "value"]
                spread["country_code"]   = "USA"
                spread["indicator_code"] = "YIELD_SPREAD_10Y3M"
                spread["period_type"]    = "monthly"
                spread["source_name"]    = "FRED"
                spread["is_forecast"]    = False
                frames.append(spread)
                print(f"  → {len(spread)} obs. Yield Spread 10Y-3M calculado")
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
            yf_out = pd.concat(rows, ignore_index=True)
            frames.append(yf_out)
            print(f"  → {len(yf_out)} linhas yfinance expandido")
    else:
        print("⚠️  yfinance_expanded_*.csv não encontrado.")

    if not frames:
        print("Nenhum dado processado.")
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(subset=["value"])

    out_path = PROCESSED_DATA_DIR / "expanded_indicators.parquet"
    out.to_parquet(out_path, index=False)
    print(f"\nSalvo: {out_path} ({len(out):,} linhas)")
    return out


if __name__ == "__main__":
    run()