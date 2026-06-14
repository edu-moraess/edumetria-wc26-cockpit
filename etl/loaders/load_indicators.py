"""
etl/loaders/load_indicators.py
Recria as tabelas dim_* e fact_indicator_values e carrega dados.
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
    ("GDP_NOMINAL",         "PIB Nominal (EUA)",                "USD_BN",    "macro"),
    ("GDP_REAL",            "PIB Real Encadeado",               "INDEX",     "macro"),
    ("CPI",                 "CPI — Inflação",                   "INDEX",     "macro"),
    ("UNEMPLOYMENT_RATE",   "Taxa de Desemprego",               "PERCENT",   "macro"),
    ("POLICY_RATE",         "Taxa de Política Monetária",       "PERCENT",   "macro"),
    ("FX_INDEX",            "Índice Cambial USD",               "INDEX",     "macro"),
    ("TREASURY_10Y",        "Treasury 10 Anos",                 "PERCENT",   "macro"),
    ("TREASURY_2Y",         "Treasury 2 Anos",                  "PERCENT",   "macro"),
    ("TREASURY_3M",         "Treasury 3 Meses",                 "PERCENT",   "macro"),
    ("YIELD_SPREAD_10Y2Y",  "Yield Spread 10Y–2Y",             "PERCENT",   "macro"),
    ("YIELD_SPREAD_10Y3M",  "Yield Spread 10Y–3M",             "PERCENT",   "macro"),
    ("SAHM_RULE",           "Sahm Rule (tempo real)",           "PERCENT",   "macro"),
    ("LEADING_INDEX",       "Leading Economic Index",           "INDEX",     "macro"),
    ("RECESSION_PROB",      "Prob. Recessão Fed NY",            "PERCENT",   "macro"),
    ("SOFR_RATE",           "SOFR",                             "PERCENT",   "financeiro"),
    ("HY_SPREAD",           "High Yield Spread",                "PERCENT",   "financeiro"),
    ("MOVE_INDEX",          "MOVE Index",                       "INDEX",     "financeiro"),
    ("DEBT_TO_GDP",         "Dívida/PIB (EUA)",                 "PERCENT",   "macro"),
    ("FISCAL_DEFICIT",      "Déficit Fiscal (EUA)",             "PERCENT",   "macro"),
    ("SP500",               "S&P 500",                          "INDEX",     "financeiro"),
    ("TSX",                 "TSX Composite (Canadá)",           "INDEX",     "financeiro"),
    ("IPC_MEXICO",          "IPC México",                       "INDEX",     "financeiro"),
    ("NASDAQ",              "Nasdaq Composite",                 "INDEX",     "financeiro"),
    ("RUSSELL2000",         "Russell 2000",                     "INDEX",     "financeiro"),
    ("VIX",                 "VIX",                              "INDEX",     "geopolitica"),
    ("WTI_CRUDE",           "Petróleo WTI",                     "USD_BBL",   "geopolitica"),
    ("BRENT_CRUDE",         "Petróleo Brent",                   "USD_BBL",   "geopolitica"),
    ("NATURAL_GAS",         "Gás Natural",                      "USD_MMBTU", "geopolitica"),
    ("GOLD",                "Ouro",                             "USD_OZ",    "geopolitica"),
    ("ETF_AVIATION",        "ETF Aviação (JETS)",               "USD",       "financeiro"),
    ("ETF_LEISURE",         "ETF Lazer (PEJ)",                  "USD",       "financeiro"),
    ("ETF_CONSUMER_DISCRETIONARY", "ETF Consumo Discr. (XLY)", "USD",       "financeiro"),
    ("TOURISM_ARRIVALS",    "Chegadas Turistas Internacionais", "COUNT",     "turismo"),
    ("FX_CAD_USD",          "Câmbio CAD/USD",                   "RATE",      "macro"),
]

SOURCE_CATALOG = [
    (1, "FRED",     "institutional", "A"),
    (2, "yfinance", "market",        "B"),
    (3, "StatCan",  "institutional", "A"),
    (4, "Banxico",  "institutional", "A"),
    (5, "INEGI",    "institutional", "A"),
    (6, "BoC",      "institutional", "A"),
]

SOURCE_NAME_TO_ID = {name: sid for sid, name, _, _ in SOURCE_CATALOG}
KNOWN_CODES = {row[0] for row in INDICATOR_CATALOG}

def recreate_schema(conn):
    """Recria todas as tabelas do zero."""
    conn.execute("DROP TABLE IF EXISTS fact_indicator_values")
    conn.execute("DROP TABLE IF EXISTS dim_indicator")
    conn.execute("DROP TABLE IF EXISTS dim_source")
    conn.execute("""
        CREATE TABLE dim_indicator (
            indicator_code TEXT PRIMARY KEY,
            name TEXT,
            unit TEXT,
            category TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE dim_source (
            source_id INTEGER PRIMARY KEY,
            source_name TEXT,
            type TEXT,
            tier TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE fact_indicator_values (
            id INTEGER PRIMARY KEY,
            country_code TEXT,
            city_id TEXT,
            indicator_code TEXT,
            scenario_code TEXT,
            source_id INTEGER,
            period DATE,
            period_type TEXT,
            value REAL,
            is_forecast BOOLEAN,
            confidence_low REAL,
            confidence_high REAL,
            version INTEGER,
            FOREIGN KEY (indicator_code) REFERENCES dim_indicator(indicator_code),
            FOREIGN KEY (source_id) REFERENCES dim_source(source_id)
        )
    """)
    # Inserir dimensões
    for code, name, unit, cat in INDICATOR_CATALOG:
        conn.execute("INSERT INTO dim_indicator VALUES (?, ?, ?, ?)", [code, name, unit, cat])
    for sid, name, typ, tier in SOURCE_CATALOG:
        conn.execute("INSERT INTO dim_source VALUES (?, ?, ?, ?)", [sid, name, typ, tier])

def load_processed_file(conn, path: Path, next_id: int) -> int:
    print(f"Carregando {path.name}...")
    df = pd.read_parquet(path)

    # Limpeza
    before = len(df)
    df = df.dropna(subset=["value"])
    if (d := before - len(df)) > 0:
        print(f"  ⚠️ {d} linhas NULL removidas")

    df = df[df["indicator_code"].isin(KNOWN_CODES)]
    df["source_id"] = df["source_name"].map(SOURCE_NAME_TO_ID)
    df = df.dropna(subset=["source_id"])
    df["source_id"] = df["source_id"].astype(int)

    if df.empty:
        print(f"  ⚠️ Nenhuma linha válida, pulando.")
        return next_id

    df["scenario_code"] = "base"
    df["city_id"] = None
    df["confidence_low"] = None
    df["confidence_high"] = None
    df["version"] = 1
    df = df.reset_index(drop=True)
    df["id"] = range(next_id, next_id + len(df))

    cols = [
        "id", "country_code", "city_id", "indicator_code", "scenario_code",
        "source_id", "period", "period_type", "value", "is_forecast",
        "confidence_low", "confidence_high", "version",
    ]
    for col in cols:
        if col not in df.columns:
            df[col] = None

    insert_df = df[cols].copy()
    conn.register("insert_df", insert_df)
    conn.execute("""
        INSERT INTO fact_indicator_values
            (id, country_code, city_id, indicator_code, scenario_code,
             source_id, period, period_type, value, is_forecast,
             confidence_low, confidence_high, version)
        SELECT * FROM insert_df
    """)
    conn.unregister("insert_df")
    print(f"  → {len(insert_df):,} linhas carregadas")
    return next_id + len(insert_df)

def run():
    with get_connection() as conn:
        recreate_schema(conn)
        print("✓ Schema recriado.\n")

        files = sorted(PROCESSED_DATA_DIR.glob("*.parquet"))
        if not files:
            print("Nenhum .parquet em data/processed/")
            return

        next_id = 1
        for path in files:
            next_id = load_processed_file(conn, path, next_id)

        total = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
        print(f"\n✓ Total: {total:,} registros em fact_indicator_values")

if __name__ == "__main__":
    run()