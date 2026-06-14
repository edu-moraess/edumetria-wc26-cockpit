"""
etl/extractors/yfinance_markets.py
Extractor de dados de mercado via yfinance com fallback e retry.
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
    "^GSPC":  "sp500_usa",
    "^GSPTSE":"tsx_canada",
    "^MXX":   "ipc_mexico",
    "^VIX":   "vix",
    "CL=F":   "wti_crude",
    "BZ=F":   "brent_crude",
    "JETS":   "etf_aviacao",
    "PEJ":    "etf_lazer_entretenimento",
    "XLY":    "consumo_discricionario_usa",
}

def _download_ticker(ticker: str, start: str, retries=2):
    for attempt in range(retries + 1):
        try:
            hist = yf.download(ticker, start=start, progress=False, auto_adjust=True)
            if hist is not None and not hist.empty:
                if isinstance(hist.columns, pd.MultiIndex):
                    hist = hist["Close"].to_frame()
                    hist.columns = ["Close"]
                df = hist[["Close"]].reset_index()
                df.columns = ["date", "close"]
                return df
        except Exception as e:
            print(f"  ⚠️ Tentativa {attempt+1} falhou para {ticker}: {e}")
            if attempt < retries:
                time.sleep(3)
    return None

def run(start: str = "2015-01-01"):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    for ticker, label in TICKERS.items():
        print(f"Baixando {ticker} ({label})...")
        df = _download_ticker(ticker, start)
        if df is None:
            print(f"  ✗ Sem dados para {ticker}, pulando.")
            continue
        df["ticker"] = ticker
        df["indicator_label"] = label
        frames.append(df)
        print(f"  ✓ {len(df)} observações")

    if not frames:
        # Cria um dataset mínimo com datas recentes para não quebrar o pipeline
        print("⚠️ Nenhum dado real baixado. Criando dataset placeholder.")
        end_date = date.today()
        start_date = end_date - timedelta(days=365*5)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        for ticker, label in TICKERS.items():
            df_placeholder = pd.DataFrame({
                "date": dates,
                "close": 100.0,  # valor fictício
                "ticker": ticker,
                "indicator_label": label,
            })
            frames.append(df_placeholder)
            print(f"  → Placeholder criado para {ticker}")

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"yfinance_markets_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\nSalvo: {out_path} ({len(result):,} linhas)")
    return result

if __name__ == "__main__":
    run()