"""
dashboards/pages/05_hotelaria.py
Página 5 — Hotelaria
ADR, RevPAR, Ocupação.
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402

page_header("Hotelaria", "ADR · RevPAR · Ocupação (fonte de referência: STR Global)")

kpi_row([
    ("ADR Médio (pico)*", "US$ —", None),
    ("RevPAR (pico)*", "US$ —", None),
    ("Ocupação (pico)*", "—%", None),
    ("ADR vs. Baseline (variação)*", "—%", None),
])

st.markdown("###")

tabs = st.tabs(["Por Cidade-Sede", "Série Temporal (jun-jul 2026)", "Pipeline de Oferta"])

with tabs[0]:
    st.subheader("ADR e Ocupação por cidade-sede")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["—"], y=[None], name="ADR (US$)"))
    fig.update_layout(title="ADR por cidade-sede (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Dados STR Global por cidade-sede")

with tabs[1]:
    st.subheader("Evolução diária — ADR / RevPAR / Ocupação")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="RevPAR (US$)"))
    fig.update_layout(title="Série diária durante o evento (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Série temporal de alta frequência (STR Global)")

with tabs[2]:
    st.subheader("Pipeline de oferta hoteleira 2026-2035")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(range(2026, 2036)), y=[None] * 10, name="Novos quartos"))
    fig.update_layout(title="Expansão de oferta hoteleira pós-evento (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Avaliação de legado de infraestrutura hoteleira")
