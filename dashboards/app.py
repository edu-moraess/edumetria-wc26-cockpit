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

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: {THEME['font_family']};
        }}

        .stApp {{
            background-color: {THEME['background']};
            color: {THEME['text']};
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {THEME['surface']};
            border-right: 1px solid {THEME['border']};
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {THEME['surface']};
            border-bottom: 1px solid {THEME['border']};
            gap: 0px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent;
            color: {THEME['secondary']};
            font-family: {THEME['font_family']};
            font-size: 0.75rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            border-bottom: 2px solid transparent;
            padding: 0.5rem 1rem;
        }}
        .stTabs [aria-selected="true"] {{
            color: {THEME['primary']};
            border-bottom: 2px solid {THEME['primary']};
            background-color: transparent;
        }}

        /* Selectbox */
        .stSelectbox > div > div {{
            background-color: {THEME['surface_alt']};
            border: 1px solid {THEME['border']};
            color: {THEME['text']};
            font-family: {THEME['font_family']};
            font-size: 0.82rem;
        }}

        /* Métricas */
        [data-testid="metric-container"] {{
            background-color: {THEME['surface']};
            border: 1px solid {THEME['border']};
            border-left: 3px solid {THEME['primary']};
            border-radius: 4px;
            padding: 0.75rem 1rem;
        }}
        [data-testid="metric-container"] label {{
            color: {THEME['secondary']};
            font-family: {THEME['font_family']};
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.10em;
        }}
        [data-testid="metric-container"] [data-testid="metric-value"] {{
            color: {THEME['text']};
            font-family: {THEME['font_family']};
            font-weight: 700;
            font-size: 1.4rem;
        }}

        /* Dataframe */
        .dataframe {{
            font-family: {THEME['font_family']};
            font-size: 0.78rem;
        }}

        /* Headings */
        h1, h2, h3, h4 {{
            font-family: {THEME['font_family']};
            font-weight: 600;
            letter-spacing: 0.03em;
            color: {THEME['text']};
        }}
        h2 {{ font-size: 1.05rem; }}
        h3 {{ font-size: 0.9rem; color: {THEME['secondary']}; text-transform: uppercase; letter-spacing: 0.08em; }}

        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {THEME['surface_alt']};
            border: 1px solid {THEME['border']};
            border-radius: 4px;
            font-family: {THEME['font_family']};
            font-size: 0.78rem;
            color: {THEME['secondary']};
        }}

        /* Buttons */
        .stButton > button {{
            background-color: {THEME['surface_alt']};
            border: 1px solid {THEME['primary']};
            color: {THEME['primary']};
            font-family: {THEME['font_family']};
            font-size: 0.75rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            border-radius: 3px;
            transition: background-color 0.2s;
        }}
        .stButton > button:hover {{
            background-color: {THEME['primary']};
            color: {THEME['background']};
        }}

        /* Caption */
        .stCaption {{
            font-family: {THEME['font_family']};
            font-size: 0.70rem;
            color: {THEME['text_muted']};
        }}

        /* Info / Warning boxes */
        .stInfo, .stWarning {{
            font-family: {THEME['font_family']};
            font-size: 0.78rem;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
        ::-webkit-scrollbar-track {{ background: {THEME['background']}; }}
        ::-webkit-scrollbar-thumb {{ background: {THEME['border']}; border-radius: 2px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# SIDEBAR — HEADER
# ------------------------------------------------------------------
st.sidebar.markdown(
    f"""
    <div style="padding-bottom:1rem; border-bottom:1px solid {THEME['border']}; margin-bottom:1rem;">
        <div style="font-family:{THEME['font_family']}; font-size:0.65rem;
                    color:{THEME['secondary']}; letter-spacing:0.12em;
                    text-transform:uppercase; margin-bottom:0.3rem;">
            Edumetria Research
        </div>
        <div style="font-family:{THEME['font_family']}; font-size:1rem;
                    font-weight:700; color:{THEME['text']}; letter-spacing:0.02em;">
            WC26 Cockpit
        </div>
        <div style="font-family:{THEME['font_family']}; font-size:0.68rem;
                    color:{THEME['secondary']}; margin-top:0.2rem;">
            {BRAND['author']}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# SIDEBAR — BOTÃO ETL
# ------------------------------------------------------------------
st.sidebar.markdown(
    f"<div style='font-family:{THEME['font_family']}; font-size:0.65rem; "
    f"color:{THEME['secondary']}; text-transform:uppercase; "
    f"letter-spacing:0.10em; margin-bottom:0.5rem;'>Pipeline ETL</div>",
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

# Status do banco
from database.connection import get_connection, init_schema  # noqa: E402

try:
    init_schema()
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM fact_indicator_values"
        ).df()["n"][0]
    if count > 0:
        st.sidebar.markdown(
            f"<div style='font-family:{THEME['font_family']}; font-size:0.68rem; "
            f"color:{THEME['positive']};'>✓ {count:,} registros</div>",
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            f"<div style='font-family:{THEME['font_family']}; font-size:0.68rem; "
            f"color:{THEME['warning']};'>⚠ Banco vazio — atualizar dados</div>",
            unsafe_allow_html=True,
        )
except Exception:
    st.sidebar.markdown(
        f"<div style='font-family:{THEME['font_family']}; font-size:0.68rem; "
        f"color:{THEME['negative']};'>✗ Banco não inicializado</div>",
        unsafe_allow_html=True,
    )

st.sidebar.markdown(
    f"""
    <div style="font-family:{THEME['font_family']}; font-size:0.62rem;
                color:{THEME['text_muted']}; border-top:1px solid {THEME['border']};
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
    st.Page(PAGES_DIR / "01_executive_overview.py", title="Executive Overview", icon="🏠", default=True),
    st.Page(PAGES_DIR / "02_macroeconomia.py",       title="Macroeconomia",      icon="📈"),
    st.Page(PAGES_DIR / "03_turismo.py",              title="Turismo",            icon="🧳"),
    st.Page(PAGES_DIR / "04_aviacao.py",              title="Aviação",            icon="✈️"),
    st.Page(PAGES_DIR / "05_hotelaria.py",            title="Hotelaria",          icon="🏨"),
    st.Page(PAGES_DIR / "06_mercado_financeiro.py",   title="Mercado Financeiro", icon="💹"),
    st.Page(PAGES_DIR / "07_geopolitica.py",          title="Geopolítica",        icon="🌍"),
    st.Page(PAGES_DIR / "08_esg.py",                  title="ESG",                icon="🌱"),
    st.Page(PAGES_DIR / "09_forecast_center.py",      title="Forecast Center",    icon="🔮"),
]

nav = st.navigation(pages)
nav.run()