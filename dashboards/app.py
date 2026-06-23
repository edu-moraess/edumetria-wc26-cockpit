"""
dashboards/app.py
FIFA World Cup 2026™ — Impact Analytics Platform (Edumetria WC26 Cockpit)
VERSÃO v6: Streamlit Cloud ready — ETL via GitHub Actions, leitura otimizada

ARQUITETURA:
- Streamlit Cloud: APENAS leitura de dados (parquet/duckdb do repo ou cache)
- GitHub Actions: ETL pesado (2-3 min) roda no CI, salva artifacts
- Fallback: dados do repo quando disponíveis
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
# DETECTAR AMBIENTE (local vs Streamlit Cloud)
# ============================================================
IS_STREAMLIT_CLOUD = (
    os.getenv("STREAMLIT_SERVER_BASE_IS_MAIN_THREAD") == "true" or
    os.getenv("HOSTNAME", "").startswith("streamlit-") or
    os.getenv("STREAMLIT_SHARING") == "true"
)

# ============================================================
# CSS SEGURO
# ============================================================
try:
    st.html(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'IBM Plex Mono', 'Segoe UI', sans-serif !important; }}
    .stApp {{ background-color: {THEME["background"]}; }}
    </style>
    """)
except AttributeError:
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'IBM Plex Mono', 'Segoe UI', sans-serif !important; }}
    .stApp {{ background-color: {THEME["background"]}; }}
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _check_duckdb_has_data() -> dict:
    """Verifica se o banco DuckDB tem dados."""
    try:
        if not DUCKDB_PATH.exists():
            return {"has_data": False, "count": 0, "error": "Banco não existe"}
        
        with get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
            return {"has_data": count > 0, "count": int(count), "error": None}
    except Exception as e:
        return {"has_data": False, "count": 0, "error": str(e)}


def _check_processed_data() -> dict:
    """Verifica se há arquivos parquet processados no repo."""
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
        
        return {
            "has_data": total_rows > 0,
            "count": total_rows,
            "files": [f.name for f in files]
        }
    except Exception as e:
        return {"has_data": False, "count": 0, "error": str(e), "files": []}


def _load_data_from_parquets() -> bool:
    """Carrega dados dos parquets para o DuckDB (rápido, sem ETL)."""
    try:
        from etl.loaders.load_indicators import run as load_run
        load_run()
        return True
    except Exception as e:
        st.error(f"Erro ao carregar parquets: {e}")
        return False


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("⚽ Edumetria")
    st.subheader("WC26 Cockpit")
    st.caption(f"{BRAND['author']} · {BRAND['role']}")
    st.divider()

    # Badge de ambiente
    if IS_STREAMLIT_CLOUD:
        st.info("☁️ Streamlit Cloud — modo leitura")
    else:
        st.success("💻 Local — modo completo")

    # Status dos dados
    st.markdown("**Status dos Dados**")
    db_status = _check_duckdb_has_data()
    parquet_status = _check_processed_data()
    
    if db_status["has_data"]:
        st.success(f"✓ {db_status['count']:,} registros no banco")
    elif parquet_status["has_data"]:
        st.warning(f"⚠ {parquet_status['count']:,} registros em parquets (não carregados)")
        if st.button("📥 Carregar para banco", key="btn_load_parquet"):
            with st.spinner("Carregando..."):
                if _load_data_from_parquets():
                    st.success("✓ Dados carregados!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("✗ Falha ao carregar")
    else:
        st.error("✗ Sem dados disponíveis")

    st.divider()

    # ETL — comportamento por ambiente
    st.markdown("**Pipeline ETL**")
    
    if IS_STREAMLIT_CLOUD:
        # Streamlit Cloud: ETL não disponível (timeout)
        st.caption("ETL indisponível no Cloud (limite 60s)")
        st.markdown("""
        **Para atualizar dados:**
        1. Rode localmente: `python -m etl.run_pipeline`
        2. Commit os parquets em `data/processed/`
        3. Push para o GitHub
        4. O Cloud lê automaticamente
        """)
        
        if st.button("🔄 Recarregar página", key="btn_reload"):
            st.rerun()
            
    else:
        # Local: ETL funcional
        if "etl_running" not in st.session_state:
            st.session_state.etl_running = False
        if "etl_result" not in st.session_state:
            st.session_state.etl_result = None

        if st.button("↺ Rodar ETL completo", use_container_width=True, key="btn_etl"):
            st.session_state.etl_running = True
            st.session_state.etl_result = None

        if st.session_state.etl_running and st.session_state.etl_result is None:
            with st.spinner("ETL rodando... 2-3 minutos"):
                try:
                    from etl import run_pipeline
                    run_pipeline.run(force_refresh=True)
                    st.session_state.etl_result = "success"
                    st.session_state.etl_running = False
                    st.success("✓ ETL concluído!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.session_state.etl_result = f"error: {e}"
                    st.session_state.etl_running = False
                    st.error(f"✗ Erro: {str(e)[:200]}")
        
        elif st.session_state.etl_result == "success":
            st.success("✓ Último ETL: OK")
        elif st.session_state.etl_result and str(st.session_state.etl_result).startswith("error"):
            st.error("✗ Último ETL: falhou")

    # Limpar cache
    if st.button("🗑️ Limpar cache", use_container_width=True, key="btn_cache"):
        st.cache_data.clear()
        st.session_state.etl_running = False
        st.session_state.etl_result = None
        st.success("Cache limpo!")
        time.sleep(0.5)
        st.rerun()

    st.divider()

    # Debug (opcional)
    with st.expander("🔧 Debug"):
        st.write(f"Ambiente: {'Cloud' if IS_STREAMLIT_CLOUD else 'Local'}")
        st.write(f"DuckDB path: {DUCKDB_PATH}")
        st.write(f"DuckDB existe: {DUCKDB_PATH.exists()}")
        st.write(f"Parquets: {parquet_status.get('files', [])}")
        if db_status.get("error"):
            st.write(f"Erro DB: {db_status['error']}")

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
