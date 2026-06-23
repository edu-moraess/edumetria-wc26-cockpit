"""
dashboards/app.py
FIFA World Cup 2026™ — Impact Analytics Platform
VERSÃO v9 FINAL: Streamlit Cloud ready, todas as abas, dados mock integrados
"""

import sys
from pathlib import Path
import streamlit as st
import os
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import THEME, BRAND, PROCESSED_DATA_DIR  # noqa: E402
from database.connection import get_connection, init_schema, DUCKDB_PATH  # noqa: E402

st.set_page_config(
    page_title="FIFA 2026 Impact Analytics | Edumetria",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DETECTAR AMBIENTE
# ============================================================
IS_STREAMLIT_CLOUD = (
    os.getenv("STREAMLIT_SERVER_BASE_IS_MAIN_THREAD") == "true" or
    os.getenv("STREAMLIT_SHARING") == "true" or
    not os.access(str(ROOT_DIR / "data" / "raw"), os.W_OK)
)

# ============================================================
# CSS
# ============================================================
try:
    st.html(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'IBM Plex Mono', 'Segoe UI', sans-serif !important; }}
    .stApp {{ background-color: {THEME["background"]}; }}
    </style>
    """)
except:
    pass

# ============================================================
# FUNÇÕES DE DADOS
# ============================================================

def _check_duckdb_has_data() -> dict:
    try:
        if not DUCKDB_PATH.exists():
            return {"has_data": False, "count": 0, "error": "Banco não existe"}
        with get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
            return {"has_data": count > 0, "count": int(count), "error": None}
    except Exception as e:
        return {"has_data": False, "count": 0, "error": str(e)}


def _check_parquets() -> dict:
    try:
        files = list(PROCESSED_DATA_DIR.glob("*.parquet"))
        if not files:
            return {"has_data": False, "count": 0, "files": []}
        
        total_rows = 0
        for f in files:
            try:
                import pandas as pd
                df = pd.read_parquet(f)
                total_rows += len(df)
            except:
                pass
        
        return {"has_data": total_rows > 0, "count": total_rows, "files": [f.name for f in files]}
    except Exception as e:
        return {"has_data": False, "count": 0, "error": str(e), "files": []}


def _load_parquets_to_db() -> bool:
    try:
        from etl.loaders.load_indicators import run as load_run
        load_run()
        return True
    except Exception as e:
        st.error(f"Erro ao carregar parquets: {e}")
        return False


def _create_mock_data() -> bool:
    """Cria dados de demonstração completos para todas as abas."""
    try:
        import pandas as pd
        import numpy as np
        
        st.info("🔄 Criando dados de demonstração...")
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # 1. MACRO USA
        dates = pd.date_range("2020-01-01", "2024-12-01", freq="MS")
        np.random.seed(42)
        records = []
        for date in dates:
            records.extend([
                {"country_code": "USA", "indicator_code": "GDP_NOMINAL", "period": date, "period_type": "monthly", "value": 20000 + np.random.normal(0, 500) + (date.year - 2020) * 1000, "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "CPI", "period": date, "period_type": "monthly", "value": 250 + np.random.normal(0, 10) + (date.year - 2020) * 15, "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "UNEMPLOYMENT_RATE", "period": date, "period_type": "monthly", "value": max(2.0, 5.0 + np.random.normal(0, 1.5)), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "TREASURY_10Y", "period": date, "period_type": "monthly", "value": 3.0 + np.random.normal(0, 0.5), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "TREASURY_2Y", "period": date, "period_type": "monthly", "value": 2.5 + np.random.normal(0, 0.5), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "FEDFUNDS", "period": date, "period_type": "monthly", "value": 2.0 + np.random.normal(0, 0.3), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "CONSUMER_SENTIMENT", "period": date, "period_type": "monthly", "value": 80 + np.random.normal(0, 10), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "RETAIL_SALES", "period": date, "period_type": "monthly", "value": 500 + np.random.normal(0, 50), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "AVG_HOURLY_EARNINGS", "period": date, "period_type": "monthly", "value": 28 + np.random.normal(0, 1), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "LABOR_PARTICIPATION", "period": date, "period_type": "monthly", "value": 63 + np.random.normal(0, 1), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "POLICY_RATE", "period": date, "period_type": "monthly", "value": 2.5 + np.random.normal(0, 0.3), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "FX_INDEX", "period": date, "period_type": "monthly", "value": 100 + np.random.normal(0, 3), "source_name": "FRED", "is_forecast": False},
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
        
        # 2. MARKETS
        dates_mkt = pd.date_range("2020-01-01", "2024-12-01", freq="B")
        records_mkt = []
        for date in dates_mkt:
            records_mkt.extend([
                {"country_code": "USA", "indicator_code": "SP500", "period": date, "period_type": "daily", "value": 3500 + np.random.normal(0, 100) + (date - pd.Timestamp("2020-01-01")).days * 0.5, "source_name": "yfinance", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "NASDAQ", "period": date, "period_type": "daily", "value": 10000 + np.random.normal(0, 300) + (date - pd.Timestamp("2020-01-01")).days * 1.5, "source_name": "yfinance", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "VIX", "period": date, "period_type": "daily", "value": max(5, 20 + np.random.normal(0, 5)), "source_name": "yfinance", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "WTI_CRUDE", "period": date, "period_type": "daily", "value": 70 + np.random.normal(0, 10), "source_name": "yfinance", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "BRENT_CRUDE", "period": date, "period_type": "daily", "value": 75 + np.random.normal(0, 10), "source_name": "yfinance", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "GOLD", "period": date, "period_type": "daily", "value": 1800 + np.random.normal(0, 100), "source_name": "yfinance", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "NATURAL_GAS", "period": date, "period_type": "daily", "value": 3 + np.random.normal(0, 0.5), "source_name": "yfinance", "is_forecast": False},
                {"country_code": "CAN", "indicator_code": "TSX", "period": date, "period_type": "daily", "value": 20000 + np.random.normal(0, 500), "source_name": "yfinance", "is_forecast": False},
                {"country_code": "MEX", "indicator_code": "IPC_MEXICO", "period": date, "period_type": "daily", "value": 50000 + np.random.normal(0, 1000), "source_name": "yfinance", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "RUSSELL2000", "period": date, "period_type": "daily", "value": 2000 + np.random.normal(0, 50), "source_name": "yfinance", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "ETF_AVIATION", "period": date, "period_type": "daily", "value": 20 + np.random.normal(0, 2), "source_name": "yfinance", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "ETF_LEISURE", "period": date, "period_type": "daily", "value": 50 + np.random.normal(0, 5), "source_name": "yfinance", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "ETF_CONSUMER_DISCRETIONARY", "period": date, "period_type": "daily", "value": 150 + np.random.normal(0, 10), "source_name": "yfinance", "is_forecast": False},
            ])
        pd.DataFrame(records_mkt).to_parquet(PROCESSED_DATA_DIR / "markets.parquet", index=False)
        
        # 3. TOURISM
        dates_tour = pd.date_range("2020-01-01", "2024-12-01", freq="MS")
        records_tour = []
        for date in dates_tour:
            records_tour.extend([
                {"country_code": "CAN", "indicator_code": "TOURISM_ARRIVALS", "period": date, "period_type": "monthly", "value": 2000000 + np.random.normal(0, 200000), "source_name": "StatCan", "is_forecast": False},
                {"country_code": "MEX", "indicator_code": "TOURISM_ARRIVALS", "period": date, "period_type": "monthly", "value": 3000000 + np.random.normal(0, 300000), "source_name": "Banxico", "is_forecast": False},
            ])
        pd.DataFrame(records_tour).to_parquet(PROCESSED_DATA_DIR / "tourism.parquet", index=False)
        
        # 4. CAN/MEX MACRO
        dates_q = pd.date_range("2020-01-01", "2024-12-01", freq="QS")
        records_canmex = []
        for date in dates_q:
            records_canmex.extend([
                {"country_code": "CAN", "indicator_code": "GDP_NOMINAL", "period": date, "period_type": "quarterly", "value": 1800 + np.random.normal(0, 50), "source_name": "StatCan", "is_forecast": False},
                {"country_code": "MEX", "indicator_code": "GDP_NOMINAL", "period": date, "period_type": "quarterly", "value": 1200 + np.random.normal(0, 40), "source_name": "INEGI", "is_forecast": False},
                {"country_code": "CAN", "indicator_code": "CPI", "period": date, "period_type": "quarterly", "value": 130 + np.random.normal(0, 5), "source_name": "StatCan", "is_forecast": False},
                {"country_code": "MEX", "indicator_code": "CPI", "period": date, "period_type": "quarterly", "value": 140 + np.random.normal(0, 5), "source_name": "INEGI", "is_forecast": False},
                {"country_code": "CAN", "indicator_code": "UNEMPLOYMENT_RATE", "period": date, "period_type": "quarterly", "value": 5.5 + np.random.normal(0, 0.5), "source_name": "StatCan", "is_forecast": False},
                {"country_code": "MEX", "indicator_code": "UNEMPLOYMENT_RATE", "period": date, "period_type": "quarterly", "value": 3.5 + np.random.normal(0, 0.3), "source_name": "INEGI", "is_forecast": False},
                {"country_code": "CAN", "indicator_code": "POLICY_RATE", "period": date, "period_type": "quarterly", "value": 2.0 + np.random.normal(0, 0.2), "source_name": "BoC", "is_forecast": False},
                {"country_code": "MEX", "indicator_code": "POLICY_RATE", "period": date, "period_type": "quarterly", "value": 5.5 + np.random.normal(0, 0.3), "source_name": "Banxico", "is_forecast": False},
                {"country_code": "CAN", "indicator_code": "FX_CAD_USD", "period": date, "period_type": "quarterly", "value": 1.35 + np.random.normal(0, 0.05), "source_name": "BoC", "is_forecast": False},
                {"country_code": "MEX", "indicator_code": "FX_CAD_USD", "period": date, "period_type": "quarterly", "value": 20 + np.random.normal(0, 1), "source_name": "Banxico", "is_forecast": False},
            ])
        pd.DataFrame(records_canmex).to_parquet(PROCESSED_DATA_DIR / "macro_can_mex.parquet", index=False)
        
        # 5. EXPANDED (stress indicators)
        records_exp = []
        for date in dates:
            records_exp.extend([
                {"country_code": "USA", "indicator_code": "SOFR_RATE", "period": date, "period_type": "monthly", "value": 2.0 + np.random.normal(0, 0.2), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "HY_SPREAD", "period": date, "period_type": "monthly", "value": 4.0 + np.random.normal(0, 1), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "MOVE_INDEX", "period": date, "period_type": "monthly", "value": 80 + np.random.normal(0, 15), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "DEBT_TO_GDP", "period": date, "period_type": "monthly", "value": 120 + np.random.normal(0, 2), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "FISCAL_DEFICIT", "period": date, "period_type": "monthly", "value": 5 + np.random.normal(0, 1), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "SAHM_RULE", "period": date, "period_type": "monthly", "value": max(0, 0.2 + np.random.normal(0, 0.1)), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "LEADING_INDEX", "period": date, "period_type": "monthly", "value": 110 + np.random.normal(0, 2), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "RECESSION_PROB", "period": date, "period_type": "monthly", "value": max(0, 15 + np.random.normal(0, 5)), "source_name": "FRED", "is_forecast": False},
                {"country_code": "USA", "indicator_code": "YIELD_SPREAD_10Y3M", "period": date, "period_type": "monthly", "value": 1.0 + np.random.normal(0, 0.3), "source_name": "FRED", "is_forecast": False},
            ])
        pd.DataFrame(records_exp).to_parquet(PROCESSED_DATA_DIR / "expanded.parquet", index=False)
        
        # Carrega tudo no banco
        _load_parquets_to_db()
        
        st.success("✅ Dados de demonstração criados! Todas as abas funcionando.")
        return True
        
    except Exception as e:
        st.error(f"Erro ao criar dados mock: {e}")
        import traceback
        st.code(traceback.format_exc())
        return False


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("⚽ Edumetria")
    st.subheader("WC26 Cockpit")
    st.caption(f"{BRAND['author']} · {BRAND['role']}")
    st.divider()

    if IS_STREAMLIT_CLOUD:
        st.info("☁️ Streamlit Cloud")
    else:
        st.success("💻 Local")

    # Status dos dados
    st.markdown("**Status dos Dados**")
    db_status = _check_duckdb_has_data()
    parquet_status = _check_parquets()
    
    if db_status["has_data"]:
        st.success(f"✓ {db_status['count']:,} registros no banco")
    elif parquet_status["has_data"]:
        st.warning(f"⚠ {parquet_status['count']:,} registros em parquets")
        if st.button("📥 Carregar para banco", key="btn_load"):
            with st.spinner("Carregando..."):
                if _load_parquets_to_db():
                    st.success("✓ Carregado!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("✗ Falha")
    else:
        st.error("✗ Sem dados disponíveis")
        if st.button("🎲 Criar dados de demonstração", key="btn_mock", type="primary"):
            with st.spinner("Criando dados..."):
                if _create_mock_data():
                    time.sleep(0.5)
                    st.rerun()

    st.divider()

    # ETL
    st.markdown("**Pipeline ETL**")
    
    if IS_STREAMLIT_CLOUD:
        st.caption("ETL indisponível no Cloud (limite 60s)")
        st.markdown("""
        **Para dados reais:**
        1. Rode local: `python -m etl.run_pipeline`
        2. Commit: `git add data/processed/ && git push`
        """)
    else:
        if "etl_running" not in st.session_state:
            st.session_state.etl_running = False
        
        if st.button("↺ Rodar ETL", use_container_width=True, key="btn_etl"):
            st.session_state.etl_running = True
        
        if st.session_state.etl_running:
            with st.spinner("ETL rodando..."):
                try:
                    from etl import run_pipeline
                    run_pipeline.run(force_refresh=True)
                    st.session_state.etl_running = False
                    st.success("✓ ETL OK!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.session_state.etl_running = False
                    st.error(f"✗ Erro: {str(e)[:200]}")

    # Cache
    if st.button("🗑️ Limpar cache", use_container_width=True, key="btn_cache"):
        st.cache_data.clear()
        st.success("Cache limpo!")
        time.sleep(0.5)
        st.rerun()

    st.divider()
    st.caption("v1.0.0 · MIT License")

# ============================================================
# NAVEGAÇÃO
# ============================================================
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
