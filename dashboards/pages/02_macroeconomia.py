"""
dashboards/pages/02_macroeconomia.py
Página 2 — Macroeconomia
PIB, Inflação, Juros, Desemprego, Câmbio — por país-sede, com seletor de cenário.
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import HOST_COUNTRIES, COUNTRY_NAMES, SCENARIOS, FORECAST_START_YEAR, FORECAST_END_YEAR  # noqa: E402
from dashboards.components import page_header, apply_theme, data_pending_notice  # noqa: E402

page_header("Macroeconomia", "PIB · Inflação · Juros · Desemprego · Câmbio")

col1, col2 = st.columns([1, 1])
with col1:
    country = st.selectbox("País", [COUNTRY_NAMES[c] for c in HOST_COUNTRIES])
with col2:
    scenario = st.selectbox("Cenário", [s.capitalize() for s in SCENARIOS], index=1)

tabs = st.tabs(["PIB", "Inflação", "Juros", "Desemprego", "Câmbio"])

years = list(range(FORECAST_START_YEAR, FORECAST_END_YEAR + 1))

with tabs[0]:
    st.subheader(f"PIB — {country} ({scenario})")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=[None] * len(years), mode="lines+markers", name="PIB (var. % a.a.)"))
    fig.update_layout(title="Variação do PIB — projeção 2027-2035 (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Série de PIB por país/cenário (models/econometric)")

with tabs[1]:
    st.subheader(f"Inflação — {country} ({scenario})")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=[None] * len(years), mode="lines", name="IPC/CPI (% a.a.)"))
    fig.update_layout(title="Pressões inflacionárias localizadas vs. headline (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Decomposição de efeitos transitórios vs. persistentes")

with tabs[2]:
    st.subheader(f"Juros — {country} ({scenario})")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=[None] * len(years), mode="lines", name="Taxa de política monetária (%)"))
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Trajetória de juros (cenários BCB/Fed/Banxico/BoC)")

with tabs[3]:
    st.subheader(f"Desemprego — {country} ({scenario})")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=[None] * len(years), mode="lines", name="Taxa de desemprego (%)"))
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Empregos temporários vs. permanentes por setor")

with tabs[4]:
    st.subheader(f"Câmbio — {country} ({scenario})")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=[None] * len(years), mode="lines", name="Taxa de câmbio (vs. USD)"))
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Fluxos cambiais associados a turismo receptivo / FDI")
