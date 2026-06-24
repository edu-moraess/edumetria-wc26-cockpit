"""
etl/loaders/load_indicators.py — v5
Loader atualizado com indicadores de Aviação, Hotelaria e ESG.
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
    ("GDP_NOMINAL", "PIB Nominal", "USD_BN", "macro"),
    ("GDP_REAL", "PIB Real", "INDEX", "macro"),
    ("CPI", "CPI", "INDEX", "macro"),
    ("UNEMPLOYMENT_RATE", "Desemprego", "PERCENT", "macro"),
    ("POLICY_RATE", "Taxa de Política", "PERCENT", "macro"),
    ("FX_INDEX", "Índice Cambial", "INDEX", "macro"),
    ("TREASURY_10Y", "Treasury 10Y", "PERCENT", "macro"),
    ("TREASURY_2Y", "Treasury 2Y", "PERCENT", "macro"),
    ("YIELD_SPREAD_10Y2Y", "Yield Spread 10Y-2Y", "PERCENT", "macro"),
    ("YIELD_SPREAD_10Y3M", "Yield Spread 10Y-3M", "PERCENT", "macro"),
    ("SAHM_RULE", "Sahm Rule", "PERCENT", "macro"),
    ("LEADING_INDEX", "Leading Index", "INDEX", "macro"),
    ("RECESSION_PROB", "Prob. Recessão", "PERCENT", "macro"),
    ("CONSUMER_SENTIMENT", "Confiança Consumidor", "INDEX", "macro"),
    ("RETAIL_SALES", "Vendas Varejo", "USD_BN", "macro"),
    ("AVG_HOURLY_EARNINGS", "Salário Hora", "USD", "macro"),
    ("LABOR_PARTICIPATION", "Participação Laboral", "PERCENT", "macro"),
    ("FX_CAD_USD", "Câmbio CAD/USD", "RATE", "macro"),
    ("SP500", "S&P 500", "INDEX", "financeiro"),
    ("NASDAQ", "Nasdaq", "INDEX", "financeiro"),
    ("TSX", "TSX", "INDEX", "financeiro"),
    ("IPC_MEXICO", "IPC México", "INDEX", "financeiro"),
    ("VIX", "VIX", "INDEX", "financeiro"),
    ("RUSSELL2000", "Russell 2000", "INDEX", "financeiro"),
    ("ETF_AVIATION", "ETF Aviação", "USD", "financeiro"),
    ("ETF_LEISURE", "ETF Lazer", "USD", "financeiro"),
    ("ETF_CONSUMER_DISCRETIONARY", "ETF Consumo", "USD", "financeiro"),
    ("WTI_CRUDE", "WTI", "USD_BBL", "commodities"),
    ("BRENT_CRUDE", "Brent", "USD_BBL", "commodities"),
    ("GOLD", "Ouro", "USD_OZ", "commodities"),
    ("NATURAL_GAS", "Gás Natural", "USD_MMBTU", "commodities"),
    ("SOFR_RATE", "SOFR", "PERCENT", "stress"),
    ("HY_SPREAD", "HY Spread", "PERCENT", "stress"),
    ("MOVE_INDEX", "MOVE Index", "INDEX", "stress"),
    ("DEBT_TO_GDP", "Dívida/PIB", "PERCENT", "stress"),
    ("FISCAL_DEFICIT", "Déficit Fiscal", "PERCENT", "stress"),
    ("TOURISM_ARRIVALS", "Chegadas Turistas", "COUNT", "turismo"),
    ("AIR_TRAFFIC_TSA", "Tráfego Aéreo", "COUNT", "aviação"),
    ("JET_FUEL_PRICE", "Jet Fuel", "USD_GAL", "aviação"),
    ("LUV", "Southwest", "USD", "aviação"),
    ("DAL", "Delta", "USD", "aviação"),
    ("UAL", "United", "USD", "aviação"),
    ("AAL", "American", "USD", "aviação"),
    ("HOTEL_ADR", "ADR", "USD", "hotelaria"),
    ("HOTEL_OCCUPANCY", "Ocupação", "PERCENT", "hotelaria"),
    ("HOTEL_REVPAR", "RevPAR", "USD", "hotelaria"),
    ("MAR", "Marriott", "USD", "hotelaria"),
    ("HLT", "Hilton", "USD", "hotelaria"),
    ("H", "Hyatt", "USD", "hotelaria"),
    ("CO2_EMISSIONS", "CO₂", "MT", "esg"),
    ("ENERGY_CONSUMPTION", "Consumo Energia", "TWH", "esg"),
    ("RENEWABLE_SHARE", "Renováveis", "PERCENT", "esg"),
]

KNOWN_CODES = {row[0] for row in INDICATOR_CATALOG}


def ensure_dims(conn):
    try:
        existing = set(conn.execute("SELECT indicator_code FROM dim_indicator").df()["indicator_code"])
    except Exception:
        existing = set()
    for code, name, unit, category in INDICATOR_CATALOG:
        if code not in existing:
            try:
                conn.execute("INSERT INTO dim_indicator VALUES (?, ?, ?, ?)", [code, name, unit, category])
            except Exception:
                pass


def clear_facts(conn):
    for table in ["fact_indicator_values", "fact_montecarlo_runs", "fact_wcli"]:
        try:
            conn.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def load_file(conn, path: Path) -> int:
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        print(f"✗ Erro ao ler {path.name}: {e}")
        return 0
    df = df.dropna(subset=["value"])
    df = df[df["indicator_code"].isin(KNOWN_CODES)].copy()
    if df.empty:
        return 0
    df["source_id"] = 1
    df["scenario_code"] = "base"
    df["city_id"] = None
    df["confidence_low"] = None
    df["confidence_high"] = None
    df["is_forecast"] = df.get("is_forecast", False)
    df["version"] = 1
    cols = ["country_code", "city_id", "indicator_code", "scenario_code", "source_id", "period", "period_type", "value", "is_forecast", "confidence_low", "confidence_high", "version"]
    for col in cols:
        if col not in df.columns:
            df[col] = None
    insert_df = df[cols].copy()
    try:
        conn.register("insert_df", insert_df)
        conn.execute("""
            INSERT INTO fact_indicator_values
            (country_code, city_id, indicator_code, scenario_code, source_id, period, period_type, value, is_forecast, confidence_low, confidence_high, version)
            SELECT * FROM insert_df
        """)
        conn.unregister("insert_df")
        print(f"✓ {len(insert_df):,} linhas de {path.name}")
        return len(insert_df)
    except Exception as e:
        print(f"✗ Erro ao inserir {path.name}: {e}")
        return 0


def run():
    print("=" * 60)
    print("LOADER v5 — fact_indicator_values")
    print("=" * 60)
    init_schema()
    with get_connection() as conn:
        clear_facts(conn)
        ensure_dims(conn)
        files = sorted(PROCESSED_DATA_DIR.glob("*.parquet"))
        if not files:
            print("⚠️ Nenhum .parquet encontrado")
            return
        total = 0
        for path in files:
            total += load_file(conn, path)
        count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
        print(f"✅ Total: {count:,} registros")


if __name__ == "__main__":
    run()
