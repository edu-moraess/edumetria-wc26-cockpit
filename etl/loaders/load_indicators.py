"""
etl/loaders/load_indicators.py
Carrega todos os arquivos processados (data/processed/*.parquet) nas
tabelas dim_indicator, dim_source e fact_indicator_values do banco.

ESTRATÉGIA DE ATUALIZAÇÃO: truncate + reload.
Antes de cada carga, apaga todos os registros de fact_indicator_values
e reinicia do id=1. Isto evita duplicação quando o pipeline roda
múltiplas vezes (o banco não cresce indefinidamente).

Justificativa: o DuckDB no Streamlit Cloud é efêmero (não persiste entre
restarts), então não há histórico real a preservar — truncate é seguro.
Em produção com Postgres persistente, substituir por upsert
(INSERT ... ON CONFLICT DO UPDATE) usando a chave
(country_code, indicator_code, period, scenario_code, source_id).
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import PROCESSED_DATA_DIR  # noqa: E402
from database.connection import get_connection, init_schema  # noqa: E402

INDICATOR_CATALOG = [
    ("GDP_NOMINAL",                 "PIB Nominal",                         "USD_BN",  "macro"),
    ("GDP_REAL",                    "PIB Real (encadeado)",                 "INDEX",   "macro"),
    ("CPI",                         "Índice de Preços ao Consumidor",       "INDEX",   "macro"),
    ("UNEMPLOYMENT_RATE",           "Taxa de Desemprego",                   "PERCENT", "macro"),
    ("POLICY_RATE",                 "Taxa de Política Monetária",           "PERCENT", "macro"),
    ("FX_INDEX",                    "Índice Cambial (trade-weighted)",       "INDEX",   "macro"),
    ("TREASURY_10Y",                "Treasury 10 Anos (EUA)",              "PERCENT", "macro"),
    ("TREASURY_2Y",                 "Treasury 2 Anos (EUA)",               "PERCENT", "macro"),
    ("YIELD_SPREAD_10Y2Y",          "Yield Spread 10Y-2Y (EUA)",           "PERCENT", "macro"),
    ("SP500",                       "S&P 500",                              "INDEX",   "financeiro"),
    ("TSX",                         "TSX Composite (Canadá)",               "INDEX",   "financeiro"),
    ("IPC_MEXICO",                  "IPC México",                           "INDEX",   "financeiro"),
    ("VIX",                         "VIX — Índice de Volatilidade",         "INDEX",   "geopolitica"),
    ("WTI_CRUDE",                   "Petróleo WTI",                         "USD_BBL", "geopolitica"),
    ("BRENT_CRUDE",                 "Petróleo Brent",                       "USD_BBL", "geopolitica"),
    ("ETF_AVIATION",                "ETF Setor Aviação (JETS)",             "USD",     "financeiro"),
    ("ETF_LEISURE",                 "ETF Lazer/Entretenimento (PEJ)",       "USD",     "financeiro"),
    ("ETF_CONSUMER_DISCRETIONARY",  "ETF Consumo Discricionário (XLY)",     "USD",     "financeiro"),
    ("TOURISM_ARRIVALS",            "Chegadas de Turistas Internacionais",  "COUNT",   "turismo"),
]

SOURCE_CATALOG = [
    (1, "FRED",     "institutional", "A"),
    (2, "yfinance", "market",        "B"),
    (3, "StatCan",  "institutional", "A"),
    (4, "Banxico",  "institutional", "A"),
    (5, "INEGI",    "institutional", "A"),
]

SOURCE_NAME_TO_ID = {name: sid for sid, name, *_ in SOURCE_CATALOG}
KNOWN_CODES = {row[0] for row in INDICATOR_CATALOG}


def ensure_dims(conn):
    existing_indicators = set(
        conn.execute("SELECT indicator_code FROM dim_indicator").df()["indicator_code"]
    )
    for code, name, unit, category in INDICATOR_CATALOG:
        if code not in existing_indicators:
            conn.execute(
                "INSERT INTO dim_indicator VALUES (?, ?, ?, ?)",
                [code, name, unit, category],
            )

    existing_sources = set(
        conn.execute("SELECT source_id FROM dim_source").df()["source_id"].astype(int)
    )
    for sid, name, stype, tier in SOURCE_CATALOG:
        if sid not in existing_sources:
            conn.execute(
                "INSERT INTO dim_source VALUES (?, ?, ?, ?)",
                [sid, name, stype, tier],
            )


def load_processed_file(conn, path: Path, next_id: int) -> int:
    print(f"Carregando {path.name}...")
    df = pd.read_parquet(path)

    before = len(df)
    df = df.dropna(subset=["value"])
    if (dropped := before - len(df)) > 0:
        print(f"  ⚠️  {dropped} linhas com value=NULL removidas.")

    df = df[df["indicator_code"].isin(KNOWN_CODES)]

    df["source_id"] = df["source_name"].map(SOURCE_NAME_TO_ID)
    df = df.dropna(subset=["source_id"])
    df["source_id"] = df["source_id"].astype(int)

    if df.empty:
        print(f"  ⚠️  Nenhuma linha válida, pulando.")
        return next_id

    df["scenario_code"]   = "base"
    df["city_id"]         = None
    df["confidence_low"]  = None
    df["confidence_high"] = None
    df["version"]         = 1
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
    print(f"  → {len(insert_df)} linhas carregadas.")
    return next_id + len(insert_df)


def run():
    init_schema()

    with get_connection() as conn:
        # --- TRUNCATE antes de recarregar (evita duplicação) ---
        conn.execute("DELETE FROM fact_indicator_values")
        print("✓ fact_indicator_values limpa (truncate). Recarregando...")

        ensure_dims(conn)

        processed_files = sorted(PROCESSED_DATA_DIR.glob("*.parquet"))
        if not processed_files:
            print("Nenhum arquivo .parquet em data/processed/. "
                  "Rode os transformers primeiro.")
            return

        next_id = 1
        for path in processed_files:
            next_id = load_processed_file(conn, path, next_id)

        total = conn.execute(
            "SELECT COUNT(*) AS n FROM fact_indicator_values"
        ).df()["n"][0]
        print(f"\n✓ Total em fact_indicator_values: {total:,} linhas.")


if __name__ == "__main__":
    run()