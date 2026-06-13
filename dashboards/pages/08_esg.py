"""
dashboards/pages/08_esg.py
Página 8 — ESG
Ambiental, Social, Governança.
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402

page_header("ESG", "Ambiental · Social · Governança")

kpi_row([
    ("Emissões Estimadas (CO2e)*", "— Mt", None),
    ("Compensação de Carbono (cobertura)*", "—%", None),
    ("Empregos com Capacitação*", "—", None),
    ("Score de Governança*", "—/100", None),
])

st.markdown("###")

tabs = st.tabs(["Ambiental", "Social", "Governança"])

with tabs[0]:
    st.subheader("Pegada Ambiental")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Voos internacionais", "Energia (estádios)", "Transporte local", "Construção/Infraestrutura"],
        y=[None] * 4,
        name="Emissões (Mt CO2e)",
    ))
    fig.update_layout(title="Decomposição de emissões por fonte (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Estimativas de emissões e programas de compensação")

with tabs[1]:
    st.subheader("Impacto Social")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Inclusão", "Emprego local", "Capacitação profissional"],
                          y=[None, None, None], name="Indicador social (índice)"))
    fig.update_layout(title="Indicadores sociais (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Indicadores sociais por cidade-sede")

with tabs[2]:
    st.subheader("Governança")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Transparência", "Gestão de contratos", "Uso de recursos públicos"],
                          y=[None, None, None], name="Score (0-100)"))
    fig.update_layout(title="Score de governança por dimensão (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Avaliação qualitativa de governança e contratos públicos")
