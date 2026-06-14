"""
etl/loaders/load_indicators.py - Versão Final Robusta (14/06/2026)
"""

import sys
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import PROCESSED_DATA_DIR
from database.connection import get_connection, init_schema

INDICATOR_CATALOG = [
    ("GDP_NOMINAL", "PIB Nominal (EUA)", "USD_BN", "macro"),
    ("GDP_REAL", "PIB Real Encadeado", "INDEX", "macro"),
    ("CPI", "CPI — Inflação", "INDEX", "macro"),
    ("UNEMPLOYMENT_RATE", "Taxa de Desemprego", "PERCENT", "macro"),
    ("POLICY_RATE", "Taxa de Política Monetária", "PERCENT", "macro"),
    ("FX_INDEX", "Índice Cambial USD", "INDEX", "macro"),
    ("TREASURY_10Y", "Treasury 10 Anos", "PERCENT", "macro"),
    ("TREASURY_2Y", "Treasury 2 Anos", "PERCENT", "macro"),
    ("TREASURY_3M", "Treasury 3 Meses", "PERCENT", "macro"),
    ("YIELD_SPREAD_10Y2Y", "Yield Spread 10Y–2Y", "PERCENT", "macro"),
    ("YIELD_SPREAD_10Y3M", "Yield Spread 10Y–3M", "PERCENT", "macro"),
    ("SAHM_RULE", "Sahm Rule", "PERCENT", "macro"),
    ("LEADING_INDEX", "Leading Economic Index", "INDEX", "macro"),
    ("RECESSION_PROB", "Prob. Recessão Fed NY", "PERCENT", "macro"),
    ("SOFR_RATE", "SOFR", "PERCENT", "financeiro"),
    ("HY_SPREAD", "High Yield Spread", "PERCENT", "financeiro"),
    ("MOVE_INDEX", "MOVE Index", "INDEX", "financeiro"),
    ("SP500", "S&P 500", "INDEX", "financeiro"),
    ("TSX", "TSX Composite", "INDEX", "financeiro"),
    ("IPC_MEXICO", "IPC México", "INDEX", "financeiro"),
    ("VIX", "VIX", "INDEX", "geopolitica"),
    ("WTI_CRUDE", "Petróleo WTI", "USD_BBL", "geopolitica"),
    ("BRENT_CRUDE", "Petróleo Brent", "USD_BBL", "geopolitica"),
    ("NATURAL_GAS", "Gás Natural", "USD_MMBTU", "geopolitica"),
    ("ETF_AVIATION", "ETF Aviação", "USD", "financeiro"),
    ("ETF_LEISURE", "ETF Lazer", "USD", "financeiro"),
    ("TOURISM_ARRIVALS", "Chegadas Turistas Internacionais", "COUNT", "turismo"),
]

SOURCE_CATALOG = [
    (1, "FRED", "institutional", "A"),
    (2, "yfinance", "market", "B"),
    (3, "StatCan", "institutional", "A"),
    (4, "Banxico", "institutional", "A"),
    (5, "INEGI", "institutional", "A"),
    (6, "BoC", "institutional", "A"),
]

SOURCE_NAME_TO_ID = {name: sid for sid, name, _, _ in SOURCE_CATALOG}
KNOWN_CODES = {row[0] for row in INDICATOR_CATALOG}

def ensure_dims(conn):
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").df()["name"].tolist()
    if "dim_indicator" not in tables:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dim_indicator (
                indicator_code TEXT PRIMARY KEY, name TEXT, unit TEXT, category TEXT
            )
        """)
    if "dim_source" not in tables:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dim_source (
                source_id INTEGER PRIMARY KEY, source_name TEXT, type TEXT, tier TEXT
            )
        """)
    for code, name, unit, cat in INDICATOR_CATALOG:
        conn.execute("INSERT OR IGNORE INTO dim_indicator VALUES (?, ?, ?, ?)", [code, name, unit, cat])
    for sid, name, typ, tier in SOURCE_CATALOG:
        conn.execute("INSERT OR IGNORE INTO dim_source VALUES (?, ?, ?, ?)", [sid, name, typ, tier])

def clear_fact_tables(conn):
    print("🧹 Limpando tabelas de fatos...")
    try:
        conn.execute("TRUNCATE TABLE IF EXISTS fact_montecarlo_distribution CASCADE")
        conn.execute("TRUNCATE TABLE IF EXISTS fact_indicator_values CASCADE")
        print("✓ Limpeza com CASCADE OK.")
    except Exception:
        print("Usando DELETE fallback...")
        conn.execute("DELETE FROM fact_montecarlo_distribution")
        conn.execute("DELETE FROM fact_indicator_values")

def load_processed_file(conn, path: Path, next_id: int) -> int:
    print(f"Carregando {path.name}...")
    df = pd.read_parquet(path)
    df = df.dropna(subset=["value"])
    df = df[df["indicator_code"].isin(KNOWN_CODES)].copy()
    
    if "source_name" not in df.columns:
        df["source_name"] = "yfinance"
    df["source_id"] = df["source_name"].map(SOURCE_NAME_TO_ID)
    df = df.dropna(subset=["source_id"])
    df["source_id"] = df["source_id"].astype(int)

    df["scenario_code"] = "base"
    df["version"] = 1
    df = df.reset_index(drop=True)
    df["id"] = range(next_id, next_id + len(df))

    cols = ["id", "country_code", "indicator_code", "scenario_code", "source_id", 
            "period", "period_type", "value", "is_forecast", "version"]
    insert_df = df[cols].copy()
    
    conn.register("insert_df", insert_df)
    conn.execute("""
        INSERT INTO fact_indicator_values 
        (id, country_code, indicator_code, scenario_code, source_id, 
         period, period_type, value, is_forecast, version)
        SELECT * FROM insert_df
    """)
    conn.unregister("insert_df")
    
    print(f"  → {len(insert_df):,} linhas carregadas")
    return next_id + len(insert_df)

def run():
    init_schema()
    with get_connection() as conn:
        clear_fact_tables(conn)
        ensure_dims(conn)

        files = sorted(PROCESSED_DATA_DIR.glob("*.parquet"))
        if not files:
            print("⚠️ Nenhum .parquet em data/processed/")
            return

        next_id = 1
        for path in files:
            next_id = load_processed_file(conn, path, next_id)

        total = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
        print(f"\n✅ Total: {total:,} registros em fact_indicator_values")

if __name__ == "__main__":
    run()