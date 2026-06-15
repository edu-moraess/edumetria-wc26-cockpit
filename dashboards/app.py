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
bg          = THEME["background"]
surface     = THEME["surface"]
surface_alt = THEME["surface_alt"]
border      = THEME["border"]
primary     = THEME["primary"]
secondary   = THEME["secondary"]
text        = THEME["text"]
text_muted  = THEME["text_muted"]
positive    = THEME["positive"]
negative    = THEME["negative"]
warning     = THEME["warning"]
font        = THEME["font_family"]
author      = BRAND["author"]

# ------------------------------
# CSS customizado
# ------------------------------
st.markdown(
    f"""
    <style>
        /* estilos omitidos para brevidade, iguais ao original */
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# SIDEBAR — HEADER
# ------------------------------
st.sidebar.markdown(
    f"""
    <div style="padding-bottom:1rem; border-bottom:1px solid {border}; margin-bottom:1rem;">
        <div style="font-family:{font}; font-size:0.65rem;
                    color:{secondary}; letter-spacing:0.12em;
                    text-transform:uppercase; margin-bottom:0.3rem;">
            Edumetria Research
        </div>
        <div style="font-family:{font}; font-size:1rem;
                    font-weight:700; color:{text}; letter-spacing:0.02em;">
            WC26 Cockpit
        </div>
        <div style="font-family:{font}; font-size:0.68rem;
                    color:{secondary}; margin-top:0.2rem;">
            {author}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# SIDEBAR — BOTÃO ETL
# ------------------------------
st.sidebar.markdown("<div style='font-size:0.65rem;'>Pipeline ETL</div>", unsafe_allow_html=True)

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
            st.sidebar.success("✓ Dados atualizados")
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

if st.sidebar.button("🗑️ Limpar cache", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.success("Cache limpo! Recarregue a página.")

# ------------------------------
# SIDEBAR — STATUS DO BANCO
# ------------------------------
try:
    init_schema()
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
    if count > 0:
        st.sidebar.markdown(f"<div style='color:{positive};'>✓ {count:,} registros</div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"<div style='color:{warning};'>⚠ Banco vazio — atualizar dados</div>", unsafe_allow_html=True)
except Exception:
    st.sidebar.markdown(f"<div style='color:{negative};'>✗ Banco não inicializado</div>", unsafe_allow_html=True)

# ------------------------------
# NAVEGAÇÃO
# ------------------------------
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
    st.Page(PAGES_DIR / "10_recession_monitor.py",    title="Recession Monitor",   icon="🚨"),
]
nav = st.navigation(pages)
nav.run()

# ------------------------------
# BLOCO DE DADOS DIRETO NO APP
# ------------------------------
st.header("📊 Dados Recentes — Indicadores WC26")

try:
    with get_connection() as conn:
        df = conn.execute("""
            SELECT country_code, indicator_code, value, ingested_at
            FROM fact_indicator_values
            ORDER BY ingested_at DESC
            LIMIT 20
        """).fetchdf()

    if df.empty:
        st.warning("⚠ Nenhum dado disponível — rode o pipeline ETL.")
    else:
        st.metric("Total de Registros", f"{len(df):,}")
        st.dataframe(df)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")