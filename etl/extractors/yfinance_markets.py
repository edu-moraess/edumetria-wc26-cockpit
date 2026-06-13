"""
etl/extractors/yfinance_markets.py
Extractor de dados de mercado financeiro via yfinance (sem API key).

Cobre página 6 (Mercado Financeiro):
- Índices nacionais dos 3 países-sede
- Setores relevantes (turismo, hotelaria, aviação, entretenimento)
- WTI/Brent (página 7 - Geopolítica)
- VIX (página 7 - Geopolítica)
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

# Tickers de interesse
TICKERS = {
    # Índices nacionais (países-sede)
    "^GSPC": "sp500_usa",
    "^GSPTSE": "tsx_canada",
    "^MXX": "ipc_mexico",

    # Risco / Geopolítica
    "^VIX": "vix",
    "CL=F": "wti_crude",
    "BZ=F": "brent_crude",

    # Setores (ETFs como proxy)
    "XLY": "consumo_discricionario_usa",   # inclui turismo/lazer
    "JETS": "etf_aviacao",
    "PEJ": "etf_lazer_entretenimento",
}


def run(start: str = "2015-01-01"):
    """Baixa séries diárias de todos os tickers e salva em data/raw/."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    frames = []
    for ticker, label in TICKERS.items():
        print(f"Baixando {ticker} ({label})...")
        hist = yf.download(ticker, start=start, progress=False)
        if hist.empty:
            print(f"  ⚠️  Sem dados para {ticker}, pulando.")
            continue

        df = hist[["Close"]].reset_index()
        df.columns = ["date", "close"]
        df["ticker"] = ticker
        df["indicator_label"] = label
        frames.append(df)

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"yfinance_markets_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} ({len(result)} linhas)")
    return result


if __name__ == "__main__":
    run()
