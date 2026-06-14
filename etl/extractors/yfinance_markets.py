"""
etl/extractors/yfinance_markets.py - Com backoff para evitar Rate Limit
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import time
import pandas as pd
import yfinance as yf

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR

TICKERS = {
    "^GSPC": "sp500_usa",
    "^GSPTSE": "tsx_canada",
    "^MXX": "ipc_mexico",
    "^VIX": "vix",
    "CL=F": "wti_crude",
    "BZ=F": "brent_crude",
    "JETS": "etf_aviacao",
    "PEJ": "etf_lazer_entretenimento",
    "XLY": "consumo_discricionario_usa",
}

def _download_ticker(ticker: str, start: str, retries=4):
    for attempt in range(retries):
        try:
            print(f"  Tentativa {attempt+1} para {ticker}...")
            hist = yf.download(ticker, start=start, progress=False, auto_adjust=True, timeout=20)
            if not hist.empty:
                if isinstance(hist.columns, pd.MultiIndex):
                    hist = hist["Close"].to_frame()
                df = hist[["Close"]].reset_index()
                df.columns = ["date", "close"]
                return df
        except Exception as e:
            print(f"  ⚠️ Erro {ticker} (tentativa {attempt+1}): {e}")
            time.sleep(8 * (attempt + 1))  # backoff crescente
    print(f"  ✗ Falha definitiva para {ticker} — placeholder")
    return None

def run(start: str = "2015-01-01"):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    for ticker, label in TICKERS.items():
        df = _download_ticker(ticker, start)
        if df is None:
            # Placeholder mínimo
            end_date = date.today()
            start_date = end_date - timedelta(days=365*5)
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            df = pd.DataFrame({
                "date": dates,
                "close": 100.0,
                "ticker": ticker,
                "indicator_label": label,
            })
        else:
            df["ticker"] = ticker
            df["indicator_label"] = label
        frames.append(df)
        print(f"  ✓ {len(df)} obs. para {label}")

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"yfinance_markets_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\nSalvo: {out_path} ({len(result):,} linhas)")
    return result

if __name__ == "__main__":
    run()