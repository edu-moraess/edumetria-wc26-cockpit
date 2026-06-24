"""
dashboards/app.py — v10.0.0
Entry point profissional. Prioriza dados reais, fallback controlado.
"""
import sys
from pathlib import Path
import streamlit as st
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import BRAND, PROCESSED_DATA_DIR
from database.connection import get_connection, init_schema, DUCKDB_PATH

st.set_page_config(
    page_title="FIFA 2026 Impact Analytics | Edumetria",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

IS_STREAMLIT_CLOUD = (
    os.getenv("STREAMLIT_SERVER_BASE_IS_MAIN_THREAD") == "true"
    or os.getenv("STREAMLIT_SHARING") == "true"
)


def _check_db() -> dict:
    try:
        if not DUCKDB_PATH.exists():
            return {"has_data": False, "count": 0}
        with get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) AS n FROM fact_indicator_values"
            ).df()["n"][0]
            return {"has_data": count > 0, "count": int(count)}
    except Exception:
        return {"has_data": False, "count": 0}


def _check_parquets() -> dict:
    try:
        files = list(PROCESSED_DATA_DIR.glob("*.parquet"))
        if not files:
            return {"has_data": False, "count": 0}
        total = sum(len(pd.read_parquet(f)) for f in files)
        return {"has_data": total > 0, "count": total, "files": [f.name for f in files]}
    except Exception:
        return {"has_data": False, "count": 0}


def _load_parquets() -> bool:
    try:
        from etl.loaders.load_indicators import run as load_run
        load_run()
        return True
    except Exception as e:
        st.error(f"Erro ao carregar parquets: {e}")
        return False


def _create_mock() -> bool:
    import pandas as pd
    import numpy as np
    
    st.info("🔄 Criando dados de demonstração profissionais...")
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    np.random.seed(42)
    dates_m = pd.date_range("2020-01-01", "2024-12-01", freq="MS")
    dates_d = pd.date_range("2020-01-01", "2024-12-01", freq="B")
    dates_q = pd.date_range("2020-01-01", "2024-12-01", freq="QS")
    
    records = []
    for d in dates_m:
        y = d.year
        records.extend([
            {"country_code": "USA", "indicator_code": "GDP_NOMINAL", "period": d, "period_type": "monthly", "value": 21000 + (y-2020)*800 + np.random.normal(0, 300), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "CPI", "period": d, "period_type": "monthly", "value": 260 + (y-2020)*12 + np.random.normal(0, 5), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "UNEMPLOYMENT_RATE", "period": d, "period_type": "monthly", "value": max(3.0, 6.0 - (y-2020)*0.5 + np.random.normal(0, 0.3)), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "POLICY_RATE", "period": d, "period_type": "monthly", "value": 2.5 + (y-2020)*0.8 + np.random.normal(0, 0.2), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "TREASURY_10Y", "period": d, "period_type": "monthly", "value": 3.0 + np.random.normal(0, 0.4), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "TREASURY_2Y", "period": d, "period_type": "monthly", "value": 2.8 + np.random.normal(0, 0.4), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "CONSUMER_SENTIMENT", "period": d, "period_type": "monthly", "value": 80 + np.random.normal(0, 8), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "RETAIL_SALES", "period": d, "period_type": "monthly", "value": 520 + np.random.normal(0, 40), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "AVG_HOURLY_EARNINGS", "period": d, "period_type": "monthly", "value": 29 + (y-2020)*0.5 + np.random.normal(0, 0.3), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "LABOR_PARTICIPATION", "period": d, "period_type": "monthly", "value": 63 + np.random.normal(0, 0.5), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "FX_INDEX", "period": d, "period_type": "monthly", "value": 100 + np.random.normal(0, 2), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "SAHM_RULE", "period": d, "period_type": "monthly", "value": max(0, 0.3 + np.random.normal(0, 0.1)), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "LEADING_INDEX", "period": d, "period_type": "monthly", "value": 110 + np.random.normal(0, 1.5), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "RECESSION_PROB", "period": d, "period_type": "monthly", "value": max(0, 12 + np.random.normal(0, 4)), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "SOFR_RATE", "period": d, "period_type": "monthly", "value": 2.2 + np.random.normal(0, 0.2), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "HY_SPREAD", "period": d, "period_type": "monthly", "value": 4.5 + np.random.normal(0, 0.8), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "MOVE_INDEX", "period": d, "period_type": "monthly", "value": 85 + np.random.normal(0, 12), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "DEBT_TO_GDP", "period": d, "period_type": "monthly", "value": 122 + np.random.normal(0, 1.5), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "FISCAL_DEFICIT", "period": d, "period_type": "monthly", "value": 5.2 + np.random.normal(0, 0.8), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "YIELD_SPREAD_10Y3M", "period": d, "period_type": "monthly", "value": 1.2 + np.random.normal(0, 0.3), "source_name": "FRED", "is_forecast": False},
            {"country_code": "CAN", "indicator_code": "TOURISM_ARRIVALS", "period": d, "period_type": "monthly", "value": 2100000 + (y-2020)*50000 + np.random.normal(0, 150000), "source_name": "StatCan", "is_forecast": False},
            {"country_code": "MEX", "indicator_code": "TOURISM_ARRIVALS", "period": d, "period_type": "monthly", "value": 3200000 + (y-2020)*80000 + np.random.normal(0, 200000), "source_name": "Banxico", "is_forecast": False},
        ])
    
    df_macro = pd.DataFrame(records)
    t10 = df_macro[df_macro["indicator_code"] == "TREASURY_10Y"].set_index("period")["value"]
    t2 = df_macro[df_macro["indicator_code"] == "TREASURY_2Y"].set_index("period")["value"]
    spread = (t10 - t2).dropna().reset_index()
    spread.columns = ["period", "value"]
    spread["country_code"] = "USA"
    spread["indicator_code"] = "YIELD_SPREAD_10Y2Y"
    spread["period_type"] = "monthly"
    spread["source_name"] = "FRED"
    spread["is_forecast"] = False
    df_macro = pd.concat([df_macro, spread], ignore_index=True)
    df_macro.to_parquet(PROCESSED_DATA_DIR / "macro_usa.parquet", index=False)
    
    records_mkt = []
    for d in dates_d:
        y = d.year
        records_mkt.extend([
            {"country_code": "USA", "indicator_code": "SP500", "period": d, "period_type": "daily", "value": 3800 + (y-2020)*400 + np.random.normal(0, 80), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "NASDAQ", "period": d, "period_type": "daily", "value": 11000 + (y-2020)*1500 + np.random.normal(0, 250), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "VIX", "period": d, "period_type": "daily", "value": max(10, 20 + np.random.normal(0, 6)), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "WTI_CRUDE", "period": d, "period_type": "daily", "value": 70 + np.random.normal(0, 8), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "BRENT_CRUDE", "period": d, "period_type": "daily", "value": 75 + np.random.normal(0, 8), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "GOLD", "period": d, "period_type": "daily", "value": 1800 + (y-2020)*80 + np.random.normal(0, 60), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "NATURAL_GAS", "period": d, "period_type": "daily", "value": 3.5 + np.random.normal(0, 0.6), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "CAN", "indicator_code": "TSX", "period": d, "period_type": "daily", "value": 21000 + (y-2020)*800 + np.random.normal(0, 400), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "MEX", "indicator_code": "IPC_MEXICO", "period": d, "period_type": "daily", "value": 52000 + (y-2020)*2000 + np.random.normal(0, 800), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "RUSSELL2000", "period": d, "period_type": "daily", "value": 2100 + (y-2020)*150 + np.random.normal(0, 50), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "ETF_AVIATION", "period": d, "period_type": "daily", "value": 22 + (y-2020)*1.5 + np.random.normal(0, 2), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "ETF_LEISURE", "period": d, "period_type": "daily", "value": 52 + (y-2020)*3 + np.random.normal(0, 4), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "ETF_CONSUMER_DISCRETIONARY", "period": d, "period_type": "daily", "value": 155 + (y-2020)*10 + np.random.normal(0, 8), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "LUV", "period": d, "period_type": "daily", "value": 45 + (y-2020)*2 + np.random.normal(0, 3), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "DAL", "period": d, "period_type": "daily", "value": 48 + (y-2020)*2.5 + np.random.normal(0, 3), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "UAL", "period": d, "period_type": "daily", "value": 52 + (y-2020)*2.8 + np.random.normal(0, 3.5), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "AAL", "period": d, "period_type": "daily", "value": 16 + (y-2020)*1 + np.random.normal(0, 1.5), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "MAR", "period": d, "period_type": "daily", "value": 165 + (y-2020)*12 + np.random.normal(0, 8), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "HLT", "period": d, "period_type": "daily", "value": 140 + (y-2020)*10 + np.random.normal(0, 6), "source_name": "yfinance", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "H", "period": d, "period_type": "daily", "value": 110 + (y-2020)*7 + np.random.normal(0, 5), "source_name": "yfinance", "is_forecast": False},
        ])
    pd.DataFrame(records_mkt).to_parquet(PROCESSED_DATA_DIR / "markets.parquet", index=False)
    
    records_cm = []
    for d in dates_q:
        y = d.year
        records_cm.extend([
            {"country_code": "CAN", "indicator_code": "GDP_NOMINAL", "period": d, "period_type": "quarterly", "value": 1850 + (y-2020)*40 + np.random.normal(0, 30), "source_name": "StatCan", "is_forecast": False},
            {"country_code": "MEX", "indicator_code": "GDP_NOMINAL", "period": d, "period_type": "quarterly", "value": 1250 + (y-2020)*35 + np.random.normal(0, 25), "source_name": "INEGI", "is_forecast": False},
            {"country_code": "CAN", "indicator_code": "CPI", "period": d, "period_type": "quarterly", "value": 132 + (y-2020)*4 + np.random.normal(0, 2), "source_name": "StatCan", "is_forecast": False},
            {"country_code": "MEX", "indicator_code": "CPI", "period": d, "period_type": "quarterly", "value": 142 + (y-2020)*5 + np.random.normal(0, 2), "source_name": "INEGI", "is_forecast": False},
            {"country_code": "CAN", "indicator_code": "UNEMPLOYMENT_RATE", "period": d, "period_type": "quarterly", "value": 5.2 + np.random.normal(0, 0.3), "source_name": "StatCan", "is_forecast": False},
            {"country_code": "MEX", "indicator_code": "UNEMPLOYMENT_RATE", "period": d, "period_type": "quarterly", "value": 3.4 + np.random.normal(0, 0.2), "source_name": "INEGI", "is_forecast": False},
            {"country_code": "CAN", "indicator_code": "POLICY_RATE", "period": d, "period_type": "quarterly", "value": 2.1 + np.random.normal(0, 0.2), "source_name": "BoC", "is_forecast": False},
            {"country_code": "MEX", "indicator_code": "POLICY_RATE", "period": d, "period_type": "quarterly", "value": 5.5 + np.random.normal(0, 0.3), "source_name": "Banxico", "is_forecast": False},
            {"country_code": "CAN", "indicator_code": "FX_CAD_USD", "period": d, "period_type": "quarterly", "value": 1.34 + np.random.normal(0, 0.04), "source_name": "BoC", "is_forecast": False},
            {"country_code": "MEX", "indicator_code": "FX_CAD_USD", "period": d, "period_type": "quarterly", "value": 20.5 + np.random.normal(0, 0.8), "source_name": "Banxico", "is_forecast": False},
        ])
    pd.DataFrame(records_cm).to_parquet(PROCESSED_DATA_DIR / "macro_can_mex.parquet", index=False)
    
    records_exp = []
    for d in dates_m:
        records_exp.extend([
            {"country_code": "USA", "indicator_code": "SOFR_RATE", "period": d, "period_type": "monthly", "value": 2.3 + np.random.normal(0, 0.2), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "HY_SPREAD", "period": d, "period_type": "monthly", "value": 4.5 + np.random.normal(0, 0.8), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "MOVE_INDEX", "period": d, "period_type": "monthly", "value": 85 + np.random.normal(0, 12), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "DEBT_TO_GDP", "period": d, "period_type": "monthly", "value": 122 + np.random.normal(0, 1.5), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "FISCAL_DEFICIT", "period": d, "period_type": "monthly", "value": 5.2 + np.random.normal(0, 0.8), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "SAHM_RULE", "period": d, "period_type": "monthly", "value": max(0, 0.3 + np.random.normal(0, 0.1)), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "LEADING_INDEX", "period": d, "period_type": "monthly", "value": 110 + np.random.normal(0, 1.5), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "RECESSION_PROB", "period": d, "period_type": "monthly", "value": max(0, 12 + np.random.normal(0, 4)), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "YIELD_SPREAD_10Y3M", "period": d, "period_type": "monthly", "value": 1.2 + np.random.normal(0, 0.3), "source_name": "FRED", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "CO2_EMISSIONS", "period": d, "period_type": "monthly", "value": 5000 + np.random.normal(0, 100), "source_name": "WorldBank", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "ENERGY_CONSUMPTION", "period": d, "period_type": "monthly", "value": 95000 + np.random.normal(0, 2000), "source_name": "WorldBank", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "RENEWABLE_SHARE", "period": d, "period_type": "monthly", "value": 22 + (d.year-2020)*0.8 + np.random.normal(0, 0.5), "source_name": "WorldBank", "is_forecast": False},
            {"country_code": "CAN", "indicator_code": "CO2_EMISSIONS", "period": d, "period_type": "monthly", "value": 550 + np.random.normal(0, 15), "source_name": "WorldBank", "is_forecast": False},
            {"country_code": "MEX", "indicator_code": "CO2_EMISSIONS", "period": d, "period_type": "monthly", "value": 480 + np.random.normal(0, 12), "source_name": "WorldBank", "is_forecast": False},
            {"country_code": "CAN", "indicator_code": "RENEWABLE_SHARE", "period": d, "period_type": "monthly", "value": 68 + (d.year-2020)*1.2 + np.random.normal(0, 0.8), "source_name": "WorldBank", "is_forecast": False},
            {"country_code": "MEX", "indicator_code": "RENEWABLE_SHARE", "period": d, "period_type": "monthly", "value": 21 + (d.year-2020)*0.6 + np.random.normal(0, 0.4), "source_name": "WorldBank", "is_forecast": False},
        ])
    pd.DataFrame(records_exp).to_parquet(PROCESSED_DATA_DIR / "expanded.parquet", index=False)
    
    records_tour = []
    for d in dates_m:
        records_tour.extend([
            {"country_code": "CAN", "indicator_code": "TOURISM_ARRIVALS", "period": d, "period_type": "monthly", "value": 2100000 + np.random.normal(0, 150000), "source_name": "StatCan", "is_forecast": False},
            {"country_code": "MEX", "indicator_code": "TOURISM_ARRIVALS", "period": d, "period_type": "monthly", "value": 3200000 + np.random.normal(0, 200000), "source_name": "Banxico", "is_forecast": False},
        ])
    pd.DataFrame(records_tour).to_parquet(PROCESSED_DATA_DIR / "tourism.parquet", index=False)
    
    records_av = []
    for d in dates_m:
        records_av.extend([
            {"country_code": "USA", "indicator_code": "AIR_TRAFFIC_TSA", "period": d, "period_type": "monthly", "value": 65 + (d.year-2020)*8 + np.random.normal(0, 5), "source_name": "TSA", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "JET_FUEL_PRICE", "period": d, "period_type": "monthly", "value": 2.8 + np.random.normal(0, 0.4), "source_name": "yfinance", "is_forecast": False},
        ])
    pd.DataFrame(records_av).to_parquet(PROCESSED_DATA_DIR / "aviation.parquet", index=False)
    
    records_hotel = []
    for d in dates_m:
        records_hotel.extend([
            {"country_code": "USA", "indicator_code": "HOTEL_ADR", "period": d, "period_type": "monthly", "value": 140 + (d.year-2020)*3 + np.random.normal(0, 5), "source_name": "STR", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "HOTEL_OCCUPANCY", "period": d, "period_type": "monthly", "value": 62 + (d.year-2020)*2 + np.random.normal(0, 3), "source_name": "STR", "is_forecast": False},
            {"country_code": "USA", "indicator_code": "HOTEL_REVPAR", "period": d, "period_type": "monthly", "value": 87 + (d.year-2020)*2.5 + np.random.normal(0, 4), "source_name": "STR", "is_forecast": False},
        ])
    pd.DataFrame(records_hotel).to_parquet(PROCESSED_DATA_DIR / "hotel.parquet", index=False)
    
    _load_parquets()
    st.success("✅ Dados de demonstração criados com sucesso!")
    return True


# ── Auto-load ──────────────────────────────────────────────────────────────
parquet_status = _check_parquets()
if parquet_status["has_data"]:
    db_status = _check_db()
    if not db_status["has_data"]:
        with st.spinner("📥 Carregando dados..."):
            if _load_parquets():
                st.rerun()

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ Edumetria")
    st.markdown("**WC26 Cockpit**")
    st.caption(f"{BRAND['author']} · {BRAND['role']}")
    st.markdown("---")
    
    db_status = _check_db()
    if db_status["has_data"]:
        st.success(f"✓ {db_status['count']:,} registros")
    else:
        st.error("✗ Sem dados")
        if st.button("🎲 Criar dados de demonstração", type="primary"):
            _create_mock()
            st.rerun()
    
    st.markdown("---")
    
    if not IS_STREAMLIT_CLOUD:
        if st.button("↺ Rodar ETL"):
            with st.spinner("ETL..."):
                try:
                    from etl import run_pipeline
                    run_pipeline.run(force_refresh=True)
                    st.success("✓ ETL concluído!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
    
    if st.button("🗑️ Limpar cache"):
        st.cache_data.clear()
        st.success("Cache limpo!")
        st.rerun()
    
    st.markdown("---")
    st.caption("v10.0.0 · MIT License")

# ── Navegação ───────────────────────────────────────────────────────────────
PAGES_DIR = Path(__file__).resolve().parent / "pages"
pages = [
    st.Page(PAGES_DIR / "01_executive_overview.py", title="Executive Overview", icon="🏠", default=True),
    st.Page(PAGES_DIR / "02_macroeconomia.py", title="Macroeconomia", icon="📈"),
    st.Page(PAGES_DIR / "03_turismo.py", title="Turismo", icon="🧳"),
    st.Page(PAGES_DIR / "04_aviacao.py", title="Aviação", icon="✈️"),
    st.Page(PAGES_DIR / "05_hotelaria.py", title="Hotelaria", icon="🏨"),
    st.Page(PAGES_DIR / "06_mercado_financeiro.py", title="Mercado Financeiro", icon="💹"),
    st.Page(PAGES_DIR / "07_geopolitica.py", title="Geopolítica", icon="🌍"),
    st.Page(PAGES_DIR / "08_esg.py", title="ESG", icon="🌱"),
    st.Page(PAGES_DIR / "09_forecast_center.py", title="Forecast Center", icon="🔮"),
    st.Page(PAGES_DIR / "10_recession_monitor.py", title="Recession Monitor", icon="🚨"),
]
nav = st.navigation(pages)
nav.run()
