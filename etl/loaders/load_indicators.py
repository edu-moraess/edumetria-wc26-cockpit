"""
etl/loaders/load_indicators.py
Carrega todos os arquivos processados (data/processed/*.parquet) nas
tabelas dim_indicator, dim_source e fact_indicator_values do banco.

ESTRATÉGIA: truncate + reload (sem duplicação).
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
    # --- Macro EUA (FRED) ---
    ("GDP_NOMINAL",           "PIB Nominal (EUA)",                    "USD_BN",  "macro"),
    ("GDP_REAL",              "PIB Real Encadeado (EUA)",              "INDEX",   "macro"),
    ("CPI",                   "CPI — Inflação (EUA)",                  "INDEX",   "macro"),
    ("UNEMPLOYMENT_RATE",     "Taxa de Desemprego (EUA)",              "PERCENT", "macro"),
    ("POLICY_RATE",           "Fed Funds Rate",                        "PERCENT", "macro"),
    ("FX_INDEX",              "Índice Cambial USD (trade-weighted)",    "INDEX",   "macro"),
    # --- Treasuries e spreads ---
    ("TREASURY_10Y",          "Treasury 10 Anos (EUA)",                "PERCENT", "macro"),
    ("TREASURY_2Y",           "Treasury 2 Anos (EUA)",                 "PERCENT", "macro"),
    ("TREASURY_3M",           "Treasury 3 Meses (EUA)",                "PERCENT", "macro"),
    ("YIELD_SPREAD_10Y2Y",    "Yield Spread 10Y–2Y (EUA)",             "PERCENT", "macro"),
    ("YIELD_SPREAD_10Y3M",    "Yield Spread 10Y–3M (EUA)",             "PERCENT", "macro"),
    # --- Recession Monitor ---
    ("SAHM_RULE",             "Sahm Rule (Recessão em Tempo Real)",    "PERCENT", "macro"),
    ("LEADING_INDEX",         "Leading Economic Index (EUA)",          "INDEX",   "macro"),
    ("RECESSION_PROB",        "Probabilidade de Recessão (EUA, %)",    "PERCENT", "macro"),
    # --- Stress financeiro ---
    ("TED_SPREAD",            "TED Spread (stress bancário)",          "PERCENT", "financeiro"),
    ("HY_SPREAD",             "High Yield Spread (crédito)",           "PERCENT", "financeiro"),
    # --- Mercado Financeiro (yfinance) ---
    ("SP500",                 "S&P 500",                               "INDEX",   "financeiro"),
    ("TSX",                   "TSX Composite (Canadá)",                "INDEX",   "financeiro"),
    ("IPC_MEXICO",            "IPC México",                            "INDEX",   "financeiro"),
    ("NASDAQ",                "Nasdaq Composite",                      "INDEX",   "financeiro"),
    ("RUSSELL2000",           "Russell 2000",                          "INDEX",   "financeiro"),
    ("VIX",                   "VIX — Volatilidade Implícita",          "INDEX",   "geopolitica"),
    ("MOVE_INDEX",            "MOVE Index — Vol. Implícita de Bonds",  "INDEX",   "financeiro"),
    # --- Energia / Commodities ---
    ("WTI_CRUDE",             "Petróleo WTI",                          "USD_BBL", "geopolitica"),
    ("BRENT_CRUDE",           "Petróleo Brent",                        "USD_BBL", "geopolitica"),
    ("NATURAL_GAS",           "Gás Natural (futuros)",                 "USD_MMBTU","geopolitica"),
    ("GOLD",                  "Ouro (futuros)",                        "USD_OZ",  "geopolitica"),
    # --- ETFs Setoriais ---
    ("ETF_AVIATION",          "ETF Aviação (JETS)",                    "USD",     "financeiro"),
    ("ETF_LEISURE",           "ETF Lazer/Entretenimento (PEJ)",        "USD",     "financeiro"),
    ("ETF_CONSUMER_DISCRETIONARY", "ETF Consumo Discricionário (XLY)","USD",     "financeiro"),
    # --- Turismo ---
    ("TOURISM_ARRIVALS",      "Chegadas Turistas Internacionais",      "COUNT",   "turismo"),
    # --- Soberania / Fiscal ---
    ("DEBT_TO_GDP",           "Dívida/PIB (EUA, %)",                   "PERCENT", "macro"),
    ("FISCAL_DEFICIT",        "Déficit Fiscal (EUA, % PIB)",           "PERCENT", "macro"),
    # --- Mercado de trabalho ---
    ("LABOR_PARTICIPATION",   "Taxa de Participação Laboral (EUA)",    "PERCENT", "macro"),
    ("AVG_HOURLY_EARNINGS",   "Salário Médio por Hora (EUA)",          "USD",     "macro"),
    # --- Cross-checks ---
    ("TREASURY_10Y_YF",       "Treasury 10Y — yfinance (cross-check)", "PERCENT", "macro"),
]

SOURCE_CATALOG = [
    (1, "FRED",     "institutional", "A"),
    (2, "yfinance", "market",        "B"),
    (3, "StatCan",  "institutional", "A"),
    (4, "Banxico",  "institutional", "A"),
    (5, "INEGI",    "institutional", "A"),
]

SOURCE_NAME_TO_ID = {name: sid for sid, name, *_ in SOURCE_CATALOG}
KNOWN_CODES       = {row[0] for row in INDICATOR_CATALOG}


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
    df     = df.dropna(subset=["value"])
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
        conn.execute("DELETE FROM fact_indicator_values")
        print("✓ fact_indicator_values limpa. Recarregando...")
        ensure_dims(conn)

        processed_files = sorted(PROCESSED_DATA_DIR.glob("*.parquet"))
        if not processed_files:
            print("Nenhum .parquet em data/processed/.")
            return

        next_id = 1
        for path in processed_files:
            next_id = load_processed_file(conn, path, next_id)

        total = conn.execute(
            "SELECT COUNT(*) AS n FROM fact_indicator_values"
        ).df()["n"][0]
        print(f"\n✓ Total: {total:,} linhas.")


if __name__ == "__main__":
    run()