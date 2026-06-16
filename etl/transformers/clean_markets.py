"""
etl/transformers/clean_markets.py

CORREÇÕES v3:
- Rejeita explicitamente linhas com close == 100.0 (placeholder)
- Rejeita séries com std == 0 (constante = dado falso)
- Log claro por indicador
- Não falha se um indicador não tiver dados
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR  # noqa: E402

INDICATOR_MAP = {
    "sp500_usa":                 ("SP500",                        "USA"),
    "tsx_canada":                ("TSX",                          "CAN"),
    "ipc_mexico":                ("IPC_MEXICO",                   "MEX"),
    "vix":                       ("VIX",                          None),
    "wti_crude":                 ("WTI_CRUDE",                    None),
    "brent_crude":               ("BRENT_CRUDE",                  None),
    "etf_aviacao":               ("ETF_AVIATION",                 None),
    "etf_lazer_entretenimento":  ("ETF_LEISURE",                  None),
    "consumo_discricionario_usa":("ETF_CONSUMER_DISCRETIONARY",   "USA"),
}

PLACEHOLDER_VALUE = 100.0


def _reject_placeholder(df: pd.DataFrame, label: str) -> pd.DataFrame:
    original = len(df)
    mask = df["close"] == PLACEHOLDER_VALUE
    if mask.any():
        print(f"  ⚠️  {label}: {mask.sum()} linhas placeholder=100.0 removidas")
        df = df[~mask]

    if df.empty:
        return df

    if df["close"].std() == 0:
        print(f"  ✗ {label}: série constante (std=0) — indicador rejeitado")
        return pd.DataFrame()

    if (original - len(df)) > 0:
        print(f"  → {label}: {original - len(df)} linhas removidas, {len(df)} válidas")

    return df


def find_latest_raw_file() -> Path | None:
    files = sorted(RAW_DATA_DIR.glob("yfinance_markets_*.csv"))
    return files[-1] if files else None


def run(input_path: Path | None = None) -> pd.DataFrame | None:
    if input_path is None:
        input_path = find_latest_raw_file()

    if input_path is None:
        print("⚠️  Nenhum arquivo yfinance_markets_*.csv — pulando transformer.")
        return None

    print(f"Lendo {input_path.name}...")
    df = pd.read_csv(input_path, parse_dates=["date"])
    print(f"  {len(df):,} linhas brutas, {df['ticker'].nunique()} tickers")

    rows = []
    for label, (indicator_code, country_code) in INDICATOR_MAP.items():
        subset = df[df["indicator_label"] == label].copy()
        if subset.empty:
            print(f"  ⚠️  {label}: sem dados no CSV")
            continue

        subset = _reject_placeholder(subset, label)
        if subset.empty:
            print(f"  ✗ {label}: sem dados válidos após rejeição")
            continue

        rows.append(pd.DataFrame({
            "country_code":   country_code,
            "indicator_code": indicator_code,
            "period":         pd.to_datetime(subset["date"]),
            "period_type":    "daily",
            "value":          subset["close"].values,
            "source_name":    "yfinance",
            "is_forecast":    False,
        }))
        print(f"  ✓ {label} ({indicator_code}): {len(subset)} linhas válidas")

    if not rows:
        print("⚠️  Nenhum dado válido de mercado")
        return None

    out = pd.concat(rows, ignore_index=True).dropna(subset=["value"])
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DATA_DIR / "markets.parquet"
    out.to_parquet(out_path, index=False)
    print(f"\n✓ Salvo: {out_path} ({len(out):,} linhas, {out['indicator_code'].nunique()} indicadores)")
    return out


if __name__ == "__main__":
    run() 