"""
etl/extractors/yfinance_markets.py
Extractor robusto de dados de mercado via yfinance.

CORREÇÕES v3:
- REMOVIDO placeholder 100.00 — se yfinance falhar, o ticker é PULADO
- Download em BATCH reduz chamadas à API e diminui Rate Limit
- Retry exponencial com jitter aleatório
- Delay configurável entre batches
- Detecção de dados suspeitos (valor constante = provável placeholder)
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

TICKERS = {
    "^GSPC":  "sp500_usa",
    "^GSPTSE": "tsx_canada",
    "^MXX":   "ipc_mexico",
    "^VIX":   "vix",
    "CL=F":   "wti_crude",
    "BZ=F":   "brent_crude",
    "JETS":   "etf_aviacao",
    "PEJ":    "etf_lazer_entretenimento",
    "XLY":    "consumo_discricionario_usa",
}

BATCH_SIZE        = 3
BATCH_DELAY       = 4
MAX_RETRIES       = 3
PLACEHOLDER_VALUE = 100.0


def _is_placeholder(df: pd.DataFrame) -> bool:
    if df.empty:
        return True
    return (df["close"] == PLACEHOLDER_VALUE).all()


def _extract_close(hist: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    if hist is None or hist.empty:
        return None
    try:
        if isinstance(hist.columns, pd.MultiIndex):
            if ticker in hist.columns.get_level_values(1):
                close_col = hist["Close"][ticker].dropna()
            elif "Close" in hist.columns.get_level_values(0):
                close_col = hist["Close"].iloc[:, 0].dropna()
            else:
                return None
        else:
            if "Close" not in hist.columns:
                return None
            close_col = hist["Close"].dropna()

        if close_col.empty:
            return None

        df = close_col.reset_index()
        df.columns = ["date", "close"]
        df["date"] = pd.to_datetime(df["date"])
        df = df.dropna()
        return df if not df.empty else None
    except Exception as e:
        print(f"  ⚠️  Erro ao extrair Close de {ticker}: {e}")
        return None


def _download_batch(tickers: list[str], start: str) -> dict[str, pd.DataFrame]:
    ticker_str = " ".join(tickers)
    try:
        hist = yf.download(
            ticker_str,
            start=start,
            progress=False,
            auto_adjust=True,
            timeout=30,
            threads=False,
        )
        results = {}
        for t in tickers:
            df = _extract_close(hist, t)
            if df is not None and not _is_placeholder(df):
                results[t] = df
                print(f"  ✓ {t}: {len(df)} observações")
            else:
                print(f"  ⚠️  {t}: sem dados válidos no batch")
        return results
    except Exception as e:
        print(f"  ⚠️  Batch falhou: {e}")
        return {}


def _download_single(ticker: str, start: str) -> pd.DataFrame | None:
    for attempt in range(1, MAX_RETRIES + 1):
        wait = (2 ** attempt) + random.uniform(0, 2)
        try:
            print(f"  [{ticker}] tentativa {attempt}/{MAX_RETRIES}...")
            hist = yf.download(
                ticker,
                start=start,
                progress=False,
                auto_adjust=True,
                timeout=20,
            )
            df = _extract_close(hist, ticker)
            if df is not None and not _is_placeholder(df):
                print(f"  ✓ {ticker}: {len(df)} obs. (individual)")
                return df
            print(f"  ⚠️  {ticker}: dado vazio ou suspeito")
        except Exception as e:
            print(f"  ⚠️  {ticker} erro (tentativa {attempt}): {e}")

        if attempt < MAX_RETRIES:
            print(f"  Aguardando {wait:.1f}s...")
            time.sleep(wait)

    print(f"  ✗ {ticker}: falhou — IGNORADO (sem placeholder)")
    return None


def run(start: str = "2015-01-01") -> pd.DataFrame | None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today  = date.today().isoformat()
    frames = []

    ticker_list = list(TICKERS.keys())
    batches     = [ticker_list[i:i + BATCH_SIZE] for i in range(0, len(ticker_list), BATCH_SIZE)]
    failed      = []

    print(f"Baixando {len(ticker_list)} tickers em {len(batches)} batches...")

    for b_idx, batch in enumerate(batches, 1):
        print(f"\n--- Batch {b_idx}/{len(batches)}: {batch} ---")
        batch_results = _download_batch(batch, start)

        for ticker in batch:
            label = TICKERS[ticker]
            if ticker in batch_results:
                df = batch_results[ticker]
            else:
                print(f"  Tentando {ticker} individualmente...")
                df = _download_single(ticker, start)

            if df is not None:
                df["ticker"]          = ticker
                df["indicator_label"] = label
                frames.append(df)
            else:
                failed.append(ticker)

        if b_idx < len(batches):
            print(f"  Aguardando {BATCH_DELAY}s...")
            time.sleep(BATCH_DELAY)

    if failed:
        print(f"\n⚠️  Tickers ignorados (sem placeholder): {failed}")

    if not frames:
        print("\n✗ Nenhum dado obtido. Pipeline continuará sem dados de mercado.")
        return None

    result   = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"yfinance_markets_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\n✓ Salvo: {out_path} ({len(result):,} linhas, {result['ticker'].nunique()} tickers)")
    return result


if __name__ == "__main__":
    run()