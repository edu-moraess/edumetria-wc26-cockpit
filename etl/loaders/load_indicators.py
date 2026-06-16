"""
etl/loaders/load_indicators.py — v3

CORREÇÕES:
- TRUNCATE CASCADE removido — DuckDB não suporta
- DELETE simples e seguro (sem FK constraints no schema v3)
- ensure_dims usa queries DuckDB nativas (não sqlite_master)
- Logging detalhado por arquivo e por categoria
- Catálogo completo de indicadores
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
    ("GDP_NOMINAL",               "PIB Nominal (EUA)",                "USD_BN",    "macro"),
    ("GDP_REAL",                  "PIB Real Encadeado",               "INDEX",     "macro"),
    ("CPI",                       "CPI — Inflação",                   "INDEX",     "macro"),
    ("UNEMPLOYMENT_RATE",         "Taxa de Desemprego",               "PERCENT",   "macro"),
    ("POLICY_RATE",               "Taxa de Política Monetária",       "PERCENT",   "macro"),
    ("FX_INDEX",                  "Índice Cambial USD",               "INDEX",     "macro"),
    ("LABOR_PARTICIPATION",       "Participação Laboral",             "PERCENT",   "macro"),
    ("AVG_HOURLY_EARNINGS",       "Salário Médio por Hora",           "USD",       "macro"),
    ("RETAIL_SALES",              "Vendas no Varejo",                 "USD_BN",    "macro"),
    ("CONSUMER_SENTIMENT",        "Confiança do Consumidor",          "INDEX",     "macro"),
    ("TREASURY_10Y",              "Treasury 10 Anos",                 "PERCENT",   "macro"),
    ("TREASURY_2Y",               "Treasury 2 Anos",                  "PERCENT",   "macro"),
    ("TREASURY_3M",               "Treasury 3 Meses",                 "PERCENT",   "macro"),
    ("TREASURY_10Y_YF",           "Treasury 10Y (yfinance)",          "PERCENT",   "macro"),
    ("YIELD_SPREAD_10Y2Y",        "Yield Spread 10Y–2Y",              "PERCENT",   "macro"),
    ("YIELD_SPREAD_10Y3M",        "Yield Spread 10Y–3M",              "PERCENT",   "macro"),
    ("SAHM_RULE",                 "Sahm Rule",                        "PERCENT",   "macro"),
    ("LEADING_INDEX",             "Leading Economic Index",           "INDEX",     "macro"),
    ("RECESSION_PROB",            "Prob. Recessão Fed NY",            "PERCENT",   "macro"),
    ("SOFR_RATE",                 "SOFR",                             "PERCENT",   "financeiro"),
    ("HY_SPREAD",                 "High Yield Spread",                "PERCENT",   "financeiro"),
    ("MOVE_INDEX",                "MOVE Index (ICE BofA via FRED)",   "INDEX",     "financeiro"),
    ("DEBT_TO_GDP",               "Dívida/PIB (EUA)",                 "PERCENT",   "macro"),
    ("FISCAL_DEFICIT",            "Déficit Fiscal (EUA)",             "PERCENT",   "macro"),
    ("SP500",                     "S&P 500",                          "INDEX",     "financeiro"),
    ("TSX",                       "TSX Composite (Canadá)",           "INDEX",     "financeiro"),
    ("IPC_MEXICO",                "IPC México",                       "INDEX",     "financeiro"),
    ("NASDAQ",                    "Nasdaq Composite",                 "INDEX",     "financeiro"),
    ("RUSSELL2000",               "Russell 2000",                     "INDEX",     "financeiro"),
    ("VIX",                       "VIX",                              "INDEX",     "geopolitica"),
    ("WTI_CRUDE",                 "Petróleo WTI",                     "USD_BBL",   "geopolitica"),
    ("BRENT_CRUDE",               "Petróleo Brent",                   "USD_BBL",   "geopolitica"),
    ("NATURAL_GAS",               "Gás Natural",                      "USD_MMBTU", "geopolitica"),
    ("GOLD",                      "Ouro",                             "USD_OZ",    "geopolitica"),
    ("ETF_AVIATION",              "ETF Aviação (JETS)",               "USD",       "financeiro"),
    ("ETF_LEISURE",               "ETF Lazer (PEJ)",                  "USD",       "financeiro"),
    ("ETF_CONSUMER_DISCRETIONARY","ETF Consumo Discr. (XLY)",         "USD",       "financeiro"),
    ("TOURISM_ARRIVALS",          "Chegadas Turistas Internacionais", "COUNT",     "turismo"),
    ("FX_CAD_USD",                "Câmbio CAD/USD",                   "RATE",      "macro"),
    ("WB_GDP_GROWTH",             "Crescimento PIB (World Bank)",     "PERCENT",   "macro"),
    ("WB_FDI_INFLOWS",            "FDI Inflows (World Bank)",         "USD",       "macro"),
    ("WB_TOURIST_ARRIVALS",       "Turismo Int. (World Bank)",        "COUNT",     "turismo"),
    ("WB_TOURISM_RECEIPTS",       "Receita Turismo (World Bank)",     "USD",       "turismo"),
]

SOURCE_CATALOG = [
    (1, "FRED",      "institutional", "A"),
    (2, "yfinance",  "market",        "B"),
    (3, "StatCan",   "institutional", "A"),
    (4, "Banxico",   "institutional", "A"),
    (5, "INEGI",     "institutional", "A"),
    (6, "BoC",       "institutional", "A"),
    (7, "WorldBank", "institutional", "A"),
]

SOURCE_NAME_TO_ID = {name: sid for sid, name, *_ in SOURCE_CATALOG}
KNOWN_CODES       = {row[0] for row in INDICATOR_CATALOG}


def ensure_dims(conn):
    try:
        existing_indicators = set(
            conn.execute("SELECT indicator_code FROM dim_indicator").df()["indicator_code"]
        )
    except Exception:
        existing_indicators = set()

    for code, name, unit, category in INDICATOR_CATALOG:
        if code not in existing_indicators:
            try:
                conn.execute(
                    "INSERT INTO dim_indicator VALUES (?, ?, ?, ?)",
                    [code, name, unit, category],
                )
            except Exception:
                pass

    try:
        existing_sources = set(
            conn.execute("SELECT source_id FROM dim_source").df()["source_id"].astype(int)
        )
    except Exception:
        existing_sources = set()

    for sid, name, stype, tier in SOURCE_CATALOG:
        if sid not in existing_sources:
            try:
                conn.execute(
                    "INSERT INTO dim_source VALUES (?, ?, ?, ?)",
                    [sid, name, stype, tier],
                )
            except Exception:
                pass


def clear_fact_tables(conn):
    print("🧹 Limpando tabelas de fatos...")
    tables = [
        "fact_montecarlo_distribution",
        "fact_montecarlo_runs",
        "fact_wcli",
        "audit_fifa_projections",
        "fact_indicator_values",
    ]
    for table in tables:
        try:
            conn.execute(f"DELETE FROM {table}")
            print(f"  ✓ {table}: limpa")
        except Exception as e:
            print(f"  ⚠️  {table}: {e}")
    print()


def load_processed_file(conn, path: Path, next_id: int) -> int:
    print(f"Carregando {path.name}...")
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        print(f"  ✗ Erro ao ler {path.name}: {e}")
        return next_id

    original_len = len(df)
    df = df.dropna(subset=["value"])
    df = df[df["indicator_code"].isin(KNOWN_CODES)].copy()

    if "source_name" not in df.columns:
        df["source_name"] = "FRED"

    df["source_id"] = df["source_name"].map(SOURCE_NAME_TO_ID)
    df = df.dropna(subset=["source_id"])
    df["source_id"] = df["source_id"].astype(int)

    if df.empty:
        print(f"  ⚠️  Nenhuma linha válida — pulando")
        return next_id

    df["scenario_code"]   = "base"
    df["city_id"]         = None
    df["confidence_low"]  = None
    df["confidence_high"] = None
    df["is_forecast"]     = df.get("is_forecast", False)
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

    try:
        conn.register("insert_df", insert_df)
        conn.execute("""
            INSERT INTO fact_indicator_values
                (id, country_code, city_id, indicator_code, scenario_code,
                 source_id, period, period_type, value, is_forecast,
                 confidence_low, confidence_high, version)
            SELECT * FROM insert_df
        """)
        conn.unregister("insert_df")
        print(f"  ✓ {len(insert_df):,} linhas carregadas")
    except Exception as e:
        print(f"  ✗ Erro ao inserir {path.name}: {e}")
        try:
            conn.unregister("insert_df")
        except Exception:
            pass
        return next_id

    return next_id + len(insert_df)


def run():
    print("=" * 60)
    print("LOADER — fact_indicator_values")
    print("=" * 60)

    init_schema()

    with get_connection() as conn:
        clear_fact_tables(conn)
        ensure_dims(conn)

        files = sorted(PROCESSED_DATA_DIR.glob("*.parquet"))
        if not files:
            print("⚠️  Nenhum .parquet em data/processed/")
            return

        print(f"{len(files)} arquivo(s) parquet encontrado(s):\n")
        next_id = 1
        for path in files:
            next_id = load_processed_file(conn, path, next_id)
            print()

        total = conn.execute(
            "SELECT COUNT(*) AS n FROM fact_indicator_values"
        ).df()["n"][0]

        print("=" * 60)
        print(f"✅ Total: {total:,} registros em fact_indicator_values")
        print("=" * 60)


if __name__ == "__main__":
    run() 