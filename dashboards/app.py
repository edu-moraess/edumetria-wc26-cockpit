"""
dashboards/app.py
FIFA World Cup 2026™ — Impact Analytics Platform (Edumetria WC26 Cockpit)
Entry point Streamlit. Define tema, navegação multi-página e header
institucional. Conteúdo de cada página em dashboards/pages/.

Executar:
    streamlit run dashboards/app.py
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
        .stApp {{
            background-color: {THEME['background']};
            color: {THEME['text']};
            font-family: {THEME['font_family']};
        }}
        section[data-testid="stSidebar"] {{
            background-color: {THEME['surface']};
            border-right: 1px solid {THEME['grid']};
        }}
        h1, h2, h3 {{
            font-weight: 600;
            letter-spacing: 0.02em;
        }}
        .kpi-card {{
            background-color: {THEME['surface']};
            border: 1px solid {THEME['grid']};
            border-radius: 6px;
            padding: 1rem 1.25rem;
        }}
        .kpi-label {{
            color: {THEME['secondary']};
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .kpi-value {{
            font-size: 1.6rem;
            font-weight: 700;
            color: {THEME['primary']};
        }}
        .institutional-footer {{
            color: {THEME['secondary']};
            font-size: 0.75rem;
            border-top: 1px solid {THEME['grid']};
            padding-top: 0.5rem;
            margin-top: 2rem;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    f"""
    <div style="padding-bottom: 1rem; border-bottom: 1px solid {THEME['grid']};
                margin-bottom: 1rem;">
        <div style="font-size: 1.1rem; font-weight: 700; color: {THEME['primary']};">
            ⚽ FIFA 2026 Impact Analytics
        </div>
        <div style="font-size: 0.75rem; color: {THEME['secondary']};">
            {BRAND['org']} · {BRAND['author']}<br>
            {BRAND['role']}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    f"""
    <div class="institutional-footer">
        Horizonte de análise: 2026–2035<br>
        Sedes: 🇺🇸 EUA · 🇨🇦 Canadá · 🇲🇽 México<br>
        Atualizado automaticamente via pipeline ETL
    </div>
    """,
    unsafe_allow_html=True,
)

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
]

nav = st.navigation(pages)
nav.run()
