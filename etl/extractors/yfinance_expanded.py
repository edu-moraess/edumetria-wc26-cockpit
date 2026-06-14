"""
etl/extractors/yfinance_expanded.py
Extractor expandido — tickers adicionais para Risk Score 2.0.

Natural Gas (NG=F): componente energético do Risk Score 2.0
MOVE Index proxy (^MOVE): volatilidade implícita de bonds
  — se não disponível via yfinance, usa ICE BofA MOVE proxy
  via FRED (BAMLMOVE1WMPIM156) — já coberto no fred_expanded.py
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
    "NG=F":    "natural_gas_futures",
    "^MOVE":   "move_index_bond_vol",
    "^IXIC":   "nasdaq_composite",
    "^RUT":    "russell_2000",
    "^TNX":    "treasury_10y_yield_yf",   # cross-check com FRED GS10
    "GC=F":    "gold_futures",
}


def run(start: str = "2015-01-01"):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today  = date.today().isoformat()
    frames = []

    for ticker, label in TICKERS_EXPANDED.items():
        print(f"Baixando {ticker} ({label})...")
        try:
            hist = yf.download(ticker, start=start, progress=False)
            if hist.empty:
                print(f"  ⚠️  Sem dados para {ticker}, pulando.")
                continue
            df = hist[["Close"]].reset_index()
            df.columns = ["date", "close"]
            df["ticker"]          = ticker
            df["indicator_label"] = label
            frames.append(df)
        except Exception as e:
            print(f"  ⚠️  Erro {ticker}: {e}")

    if not frames:
        print("Nenhum dado extraído.")
        return None

    result   = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"yfinance_expanded_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} ({len(result)} linhas)")
    return result


if __name__ == "__main__":
    run()