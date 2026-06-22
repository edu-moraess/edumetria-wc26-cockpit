"""
dashboards/app.py
FIFA World Cup 2026™ — Impact Analytics Platform (Edumetria WC26 Cockpit)
Entry point Streamlit.
"""

import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import THEME, BRAND  # noqa: E402
from database.connection import get_connection, init_schema  # noqa: E402

st.set_page_config(
    page_title="FIFA 2026 Impact Analytics | Edumetria",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Extrai variáveis do tema
bg = THEME["background"]
surface = THEME["surface"]
surface_alt = THEME["surface_alt"]
border = THEME["border"]
primary = THEME["primary"]
secondary = THEME["secondary"]
text = THEME["text"]
text_muted = THEME["text_muted"]
positive = THEME["positive"]
negative = THEME["negative"]
warning = THEME["warning"]
font = THEME["font_family"]
author = BRAND["author"]

# ------------------------------
# CSS customizado — CORRIGIDO
# ------------------------------
# Usar st.html() em vez de st.markdown() para CSS é mais seguro no Streamlit 1.28+
try:
    st.html(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family={font.replace(" ", "+")}:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: '{font}', 'Segoe UI', sans-serif !important;
    }}
    
    .stApp {{
        background-color: {bg};
    }}
    
    /* Força recálculo de layout para evitar removeChild */
    .element-container {{
        contain: layout style;
    }}
    </style>
    """)
except AttributeError:
    # Fallback para versões antigas do Streamlit
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family={font.replace(" ", "+")}:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: '{font}', 'Segoe UI', sans-serif !important; }}
    .stApp {{ background-color: {bg}; }}
    .element-container {{ contain: layout style; }}
    </style>
    """, unsafe_allow_html=True)

# ------------------------------
# SIDEBAR — HEADER (sem HTML aninhado)
# ------------------------------
with st.sidebar:
    st.markdown(f"### ⚽ Edumetria Research")
    st.markdown(f"**WC26 Cockpit**")
    st.caption(f"{author}")
    st.divider()

# ------------------------------
# SIDEBAR — BOTÃO ETL (CORRIGIDO)
# ------------------------------
with st.sidebar:
    st.markdown("**Pipeline ETL**")
    
    # Container para logs — evita recriar elementos
    log_container = st.container()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("↺ Atualizar", use_container_width=True, key="btn_etl"):
            from etl import run_pipeline
            
            with log_container:
                with st.status("Rodando pipeline ETL...", expanded=True) as status:
                    try:
                        logs = []
                        def log(msg):
                            logs.append(str(msg))
                            st.code("\n".join(logs[-10:]))
                        
                        run_pipeline.run(log=log)
                        status.update(label="✓ Dados atualizados", state="complete")
                    except Exception as e:
                        status.update(label=f"✗ Erro: {e}", state="error")
                        st.error(f"Erro no ETL: {e}")
    
    with col2:
        if st.button("🗑️ Limpar cache", use_container_width=True, key="btn_cache"):
            st.cache_data.clear()
            st.toast("Cache limpo! Recarregue a página.")

# ------------------------------
# SIDEBAR — STATUS DO BANCO (CORRIGIDO)
# ------------------------------
with st.sidebar:
    st.divider()
    st.markdown("**Status do Banco**")
    
    try:
        init_schema()
        with get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
            if count > 0:
                st.success(f"✓ {count:,} registros carregados")
            else:
                st.warning("⚠ Banco vazio — clique em 'Atualizar'")
    except Exception as e:
        st.error("✗ Banco não inicializado")
        st.caption(f"Erro: {str(e)[:50]}")

# ------------------------------
# NAVEGAÇÃO
# ------------------------------
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
