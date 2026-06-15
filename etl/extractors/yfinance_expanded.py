"""
etl/extractors/yfinance_expanded.py
Extractor expandido via yfinance — Natural Gas, Gold, Nasdaq, Russell.

CORREÇÕES v3:
- Mesmo padrão robusto do yfinance_markets.py (sem placeholder)
- ^MOVE definitivamente removido (nunca disponível de forma confiável)
"""

import sys
import time
import random
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
    "GC=F":  "gold_futures",
    "^IXIC": "nasdaq_composite",
    "^RUT":  "russell_2000",
    "^TNX":  "treasury_10y_yield_yf",
}

BATCH_DELAY       = 5
MAX_RETRIES       = 3
PLACEHOLDER_VALUE = 100.0


def _is_placeholder(df: pd.DataFrame) -> bool:
    return df.empty or (df["close"] == PLACEHOLDER_VALUE).all()


def _extract_close(hist: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    if hist is None or hist.empty:
        return None
    try:
        if isinstance(hist.columns, pd.MultiIndex):
            if ticker in hist.columns.get_level_values(1):
                close_col = hist["Close"][ticker].dropna()
            else:
                close_col = hist["Close"].iloc[:, 0].dropna()
        else:
            if "Close" not in hist.columns:
                return None
            close_col = hist["Close"].dropna()

        if close_col.empty:
            return None
        df = close_col.reset_index()
        df.columns = ["date", "close"]
        df["date"] = pd.to_datetime(df["date"])
        return df.dropna() if not df.empty else None
    except Exception as e:
        print(f"  ⚠️  Erro ao extrair Close de {ticker}: {e}")
        return None


def _download_single(ticker: str, start: str) -> pd.DataFrame | None:
    for attempt in range(1, MAX_RETRIES + 1):
        wait = (2 ** attempt) + random.uniform(0, 2)
        try:
            hist = yf.download(
                ticker, start=start, progress=False,
                auto_adjust=True, timeout=20,
            )
            df = _extract_close(hist, ticker)
            if df is not None and not _is_placeholder(df):
                return df
        except Exception as e:
            print(f"  ⚠️  {ticker} erro (tentativa {attempt}): {e}")
        if attempt < MAX_RETRIES:
            time.sleep(wait)
    return None


def run(start: str = "2015-01-01") -> pd.DataFrame | None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today  = date.today().isoformat()
    frames = []
    failed = []

    print(f"Baixando {len(TICKERS_EXPANDED)} tickers expandidos...")

    for ticker, label in TICKERS_EXPANDED.items():
        print(f"\n  Baixando {ticker} ({label})...")
        df = _download_single(ticker, start)

        if df is not None:
            df["ticker"]          = ticker
            df["indicator_label"] = label
            frames.append(df)
            print(f"  ✓ {ticker}: {len(df)} obs.")
        else:
            failed.append(ticker)
            print(f"  ✗ {ticker}: ignorado (sem placeholder)")

        time.sleep(random.uniform(2, 4))

    if failed:
        print(f"\n⚠️  Tickers ignorados: {failed}")

    if not frames:
        print("\n✗ Nenhum dado obtido.")
        return None

    result   = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"yfinance_expanded_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\n✓ Salvo: {out_path} ({len(result):,} linhas)")
    return result


if __name__ == "__main__":
    run()