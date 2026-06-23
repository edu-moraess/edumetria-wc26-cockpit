"""
dashboards/app.py
FIFA World Cup 2026™ — Impact Analytics Platform (Edumetria WC26 Cockpit)
Entry point Streamlit.
VERSÃO: Sem HTML mal formatado, dados em tempo real, sem removeChild
"""

import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import THEME, BRAND, REALTIME_ENABLED, REALTIME_REFRESH_SECONDS  # noqa: E402
from database.connection import get_connection, init_schema  # noqa: E402

st.set_page_config(
    page_title="FIFA 2026 Impact Analytics | Edumetria",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS SEGURO — via st.html() (Streamlit 1.28+) ou st.markdown
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
# SIDEBAR — SEM HTML ANINHADO (componentes nativos Streamlit)
# ============================================================
with st.sidebar:
    st.title("⚽ Edumetria")
    st.subheader("WC26 Cockpit")
    st.caption(f"{BRAND['author']} · {BRAND['role']}")
    st.divider()

    # Status do banco em tempo real
    st.markdown("**Status do Banco**")
    try:
        init_schema()
        with get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
            if count > 0:
                st.success(f"✓ {count:,} registros")
            else:
                st.warning("⚠ Banco vazio")
    except Exception:
        st.error("✗ Banco não inicializado")

    st.divider()

    # Pipeline ETL
    st.markdown("**Pipeline ETL**")
    if st.button("↺ Atualizar dados", use_container_width=True, key="btn_etl"):
        from etl import run_pipeline
        with st.status("Rodando pipeline ETL...", expanded=True) as status:
            try:
                run_pipeline.run()
                status.update(label="✓ Dados atualizados", state="complete")
                st.rerun()
            except Exception as e:
                status.update(label=f"✗ Erro: {e}", state="error")

    if st.button("🗑️ Limpar cache", use_container_width=True, key="btn_cache"):
        st.cache_data.clear()
        st.toast("Cache limpo!")
        st.rerun()

    st.divider()

    # Dados em tempo real
    if REALTIME_ENABLED:
        st.markdown(f"**🔄 Tempo Real**")
        st.caption(f"Atualização automática a cada {REALTIME_REFRESH_SECONDS // 60} min")
        if st.toggle("Ativar auto-refresh", value=True, key="toggle_realtime"):
            st_autorefresh = st.empty()
            st_autorefresh.caption("⏱️ Próxima atualização em breve...")

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
