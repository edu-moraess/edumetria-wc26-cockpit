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

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: {font};
        }}

        .stApp {{
            background-color: {bg};
            color: {text};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {surface};
            border-right: 1px solid {border};
        }}

        .stTabs [data-baseweb="tab-list"] {{
            background-color: {surface};
            border-bottom: 1px solid {border};
            gap: 0px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent;
            color: {secondary};
            font-family: {font};
            font-size: 0.75rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            border-bottom: 2px solid transparent;
            padding: 0.5rem 1rem;
        }}
        .stTabs [aria-selected="true"] {{
            color: {primary};
            border-bottom: 2px solid {primary};
            background-color: transparent;
        }}

        .stSelectbox > div > div {{
            background-color: {surface_alt};
            border: 1px solid {border};
            color: {text};
            font-family: {font};
            font-size: 0.82rem;
        }}

        [data-testid="metric-container"] {{
            background-color: {surface};
            border: 1px solid {border};
            border-left: 3px solid {primary};
            border-radius: 4px;
            padding: 0.75rem 1rem;
        }}
        [data-testid="metric-container"] label {{
            color: {secondary};
            font-family: {font};
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.10em;
        }}
        [data-testid="metric-container"] [data-testid="metric-value"] {{
            color: {text};
            font-family: {font};
            font-weight: 700;
            font-size: 1.4rem;
        }}

        .dataframe {{
            font-family: {font};
            font-size: 0.78rem;
        }}

        h1, h2, h3, h4 {{
            font-family: {font};
            font-weight: 600;
            letter-spacing: 0.03em;
            color: {text};
        }}
        h2 {{ font-size: 1.05rem; }}
        h3 {{ font-size: 0.9rem; color: {secondary}; text-transform: uppercase; letter-spacing: 0.08em; }}

        .streamlit-expanderHeader {{
            background-color: {surface_alt};
            border: 1px solid {border};
            border-radius: 4px;
            font-family: {font};
            font-size: 0.78rem;
            color: {secondary};
        }}

        .stButton > button {{
            background-color: {surface_alt};
            border: 1px solid {primary};
            color: {primary};
            font-family: {font};
            font-size: 0.75rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            border-radius: 3px;
        }}
        .stButton > button:hover {{
            background-color: {primary};
            color: {bg};
        }}

        .stCaption {{
            font-family: {font};
            font-size: 0.70rem;
            color: {text_muted};
        }}

        .stInfo, .stWarning {{
            font-family: {font};
            font-size: 0.78rem;
        }}

        ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
        ::-webkit-scrollbar-track {{ background: {bg}; }}
        ::-webkit-scrollbar-thumb {{ background: {border}; border-radius: 2px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# SIDEBAR — HEADER
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# SIDEBAR — BOTÃO ETL E LIMPAR CACHE
# ------------------------------------------------------------------
st.sidebar.markdown(
    f"""
    <div style="font-family:{font}; font-size:0.65rem;
                color:{secondary}; text-transform:uppercase;
                letter-spacing:0.10em; margin-bottom:0.5rem;">
        Pipeline ETL
    </div>
    """,
    unsafe_allow_html=True,
)

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

# Botão para limpar cache do Streamlit (útil após atualizar dados)
if st.sidebar.button("🗑️ Limpar cache", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.success("Cache limpo! Recarregue a página ou altere de aba para ver os novos dados.")

# ------------------------------------------------------------------
# SIDEBAR — STATUS DO BANCO
# ------------------------------------------------------------------
from database.connection import get_connection, init_schema  # noqa: E402

try:
    init_schema()
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM fact_indicator_values"
        ).df()["n"][0]
    if count > 0:
        st.sidebar.markdown(
            f"<div style='font-family:{font}; font-size:0.68rem; "
            f"color:{positive};'>✓ {count:,} registros</div>",
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            f"<div style='font-family:{font}; font-size:0.68rem; "
            f"color:{warning};'>⚠ Banco vazio — atualizar dados</div>",
            unsafe_allow_html=True,
        )
except Exception:
    st.sidebar.markdown(
        f"<div style='font-family:{font}; font-size:0.68rem; "
        f"color:{negative};'>✗ Banco não inicializado</div>",
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------
# SIDEBAR — FOOTER
# ------------------------------------------------------------------
st.sidebar.markdown(
    f"""
    <div style="font-family:{font}; font-size:0.62rem;
                color:{text_muted}; border-top:1px solid {border};
                padding-top:0.75rem; margin-top:1rem; line-height:1.6;">
        Horizonte: 2026–2035<br>
        🇺🇸 EUA · 🇨🇦 Canadá · 🇲🇽 México<br>
        Dados: FRED · yfinance · StatCan · Banxico
    </div>
    """,
    unsafe_allow_html=True,
)

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
    st.Page(PAGES_DIR / "10_recession_monitor.py",    title="Recession Monitor",   icon="🚨"),
]

nav = st.navigation(pages)
nav.run()