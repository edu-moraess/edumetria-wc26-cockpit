"""
dashboards/app.py — CORRIGIDO v4
Streamlit entrypoint com invalidação automática de cache após pipeline ETL.

CORREÇÕES:
- Cache invalidado automaticamente após pipeline rodar
- Verificação de frescor dos dados (última data do banco)
- Botão de atualização mais responsivo
"""

import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import THEME, BRAND  # noqa: E402
from database.connection import init_schema, get_connection  # noqa: E402

# ------------------------------------------------------------------
# CONFIG STREAMLIT
# ------------------------------------------------------------------
st.set_page_config(
    page_title="FIFA 2026 Impact Analytics Platform",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# TEMA
# ------------------------------------------------------------------
positive = THEME["positive"]
negative = THEME["negative"]
warning = THEME["warning"]
primary = THEME["primary"]

# ------------------------------------------------------------------
# SIDEBAR — HEADER
# ------------------------------------------------------------------
st.sidebar.markdown(f"## ⚽ {BRAND['report_title']}")
st.sidebar.markdown(f"**{BRAND['org']}** · {BRAND['role']}")
st.sidebar.markdown("---")

# ------------------------------------------------------------------
# SIDEBAR — PIPELINE ETL
# ------------------------------------------------------------------
st.sidebar.subheader("🔄 Pipeline ETL")

if st.sidebar.button("↺  Atualizar dados", use_container_width=True):
    from etl import run_pipeline
    log_box = st.sidebar.empty()
    logs = []
    
    def log(msg):
        logs.append(str(msg))
        log_box.code("\n".join(logs[-15:]))
    
    with st.spinner("Rodando pipeline ETL..."):
        try:
            run_pipeline.run(log=log)
            
            # ✅ CORREÇÃO 1: Invalidar cache AUTOMATICAMENTE após sucesso
            st.cache_data.clear()
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

if st.sidebar.button("🗑️ Limpar cache", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.success("Cache limpo! Recarregando...")
    st.rerun()

# ------------------------------------------------------------------
# SIDEBAR — STATUS DO BANCO
# ------------------------------------------------------------------
try:
    init_schema()
    with get_connection() as conn:
        # ✅ CORREÇÃO 2: Mostrar última data + contagem
        count_result = conn.execute(
            "SELECT COUNT(*) AS n FROM fact_indicator_values"
        ).df()
        count = count_result["n"][0] if not count_result.empty else 0
        
        # Última data no banco
        last_date_result = conn.execute(
            "SELECT MAX(period) AS last_period FROM fact_indicator_values"
        ).df()
        last_date = last_date_result["last_period"][0] if not last_date_result.empty else None
        
    if count > 0:
        st.sidebar.markdown(f"<div style='color:{positive};'>✓ {count:,} registros</div>", unsafe_allow_html=True)
        if last_date:
            last_date_str = str(last_date)[:10]  # YYYY-MM-DD
            st.sidebar.caption(f"Última data: {last_date_str}")
    else:
        st.sidebar.markdown(f"<div style='color:{warning};'>⚠ Banco vazio — atualizar dados</div>", unsafe_allow_html=True)
except Exception as e:
    st.sidebar.markdown(f"<div style='color:{negative};'>✗ Banco não inicializado: {str(e)[:50]}</div>", unsafe_allow_html=True)

st.sidebar.markdown("---")

# ------------------------------------------------------------------
# NAVEGAÇÃO
# ------------------------------------------------------------------
PAGES_DIR = Path(__file__).resolve().parent / "pages"
pages = [
    st.Page(PAGES_DIR / "01_executive_overview.py",  title="Executive Overview",  icon="🏠", default=True),
    st.Page(PAGES_DIR / "02_macroeconomia.py",        title="Macroeconomia",       icon="📈"),
    st.Page(PAGES_DIR / "03_turismo.py",              title="Turismo",             icon="🧳"),
    st.Page(PAGES_DIR / "04_aviacao.py",              title="Aviação",             icon="✈️"),
    st.Page(PAGES_DIR / "05_hotelaria.py",            title="Hotelaria",           icon="🏨"),
    st.Page(PAGES_DIR / "06_mercado_financeiro.py",   title="Mercado Financeiro",  icon="💹"),
    st.Page(PAGES_DIR / "07_geopolitica.py",          title="Geopolítica",         icon="🌍"),
    st.Page(PAGES_DIR / "08_esg.py",                  title="ESG",                 icon="🌱"),
    st.Page(PAGES_DIR / "09_forecast_center.py",      title="Forecast Center",     icon="🔮"),
    st.Page(PAGES_DIR / "10_recession_monitor.py",    title="Recession Monitor",   icon="📉"),
]

pg = st.navigation(pages)
pg.run()
