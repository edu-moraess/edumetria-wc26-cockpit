"""
etl/extractors/yfinance_expanded.py
Extractor expandido — tickers adicionais via yfinance.

CORREÇÃO v2:
- ^MOVE removido (instável/indisponível no yfinance) →
  substituído por BAMLMOVE1WMPIM156 via FRED (fred_expanded.py)
- Mantém: Natural Gas, Nasdaq, Russell 2000, Gold, Treasury 10Y (cross-check)
"""

import sys
from pathlib import Path
from datetime import date

import pandas as pd
import yfinance as yf

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR  # noqa: E402

TICKERS_EXPANDED = {
    "NG=F":  "natural_gas_futures",
    "^IXIC": "nasdaq_composite",
    "^RUT":  "russell_2000",
    "GC=F":  "gold_futures",
    # Cross-check Treasury 10Y vs FRED GS10
    "^TNX":  "treasury_10y_yield_yf",
}


def run(start: str = "2015-01-01"):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today  = date.today().isoformat()
    frames = []

    for ticker, label in TICKERS_EXPANDED.items():
        print(f"Baixando {ticker} ({label})...")
        try:
            hist = yf.download(ticker, start=start, progress=False, auto_adjust=True)
            if hist.empty:
                print(f"  ⚠️  Sem dados para {ticker}, pulando.")
                continue
            # Compatibilidade yfinance >= 0.2.40 (MultiIndex columns)
            if isinstance(hist.columns, pd.MultiIndex):
                hist = hist["Close"].to_frame()
                hist.columns = ["Close"]
            df = hist[["Close"]].reset_index()
            df.columns = ["date", "close"]
            df["ticker"]          = ticker
            df["indicator_label"] = label
            frames.append(df)
            print(f"  → {len(df)} observações")
        except Exception as e:
            print(f"  ⚠️  Erro {ticker}: {e}")

    if not frames:
        print("Nenhum dado extraído do yfinance expandido.")
        return None

    result   = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"yfinance_expanded_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\nSalvo: {out_path} ({len(result):,} linhas)")
    return result


if __name__ == "__main__":
    run()