"""
dashboards/pages/04_aviacao.py
Página 4 — Aviação
Rotas, Passageiros, Assentos.
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402

page_header("Aviação", "Rotas · Passageiros · Assentos")

kpi_row([
    ("Rotas Adicionais*", "—", None),
    ("Passageiros Incrementais*", "—", None),
    ("Assentos Ofertados (variação)*", "—%", None),
    ("Load Factor (pico)*", "—%", None),
])

st.markdown("###")

tabs = st.tabs(["Capacidade por Hub", "Sazonalidade", "Custos Operacionais"])

with tabs[0]:
    st.subheader("Capacidade adicional por hub aeroportuário (cidades-sede)")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["—"], y=[None], name="Assentos adicionais"))
    fig.update_layout(title="Assentos adicionais por aeroporto-sede (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Dados de capacidade por aeroporto-sede (OAG / IATA)")

with tabs[1]:
    st.subheader("Sazonalidade de passageiros — junho/julho 2026")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="Passageiros/dia"))
    fig.update_layout(title="Curva de chegada/saída de passageiros (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Curva diária de passageiros durante o evento")

with tabs[2]:
    st.subheader("Custos operacionais — sensibilidade ao petróleo")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="Custo de combustível (% receita)"))
    fig.update_layout(title="Sensibilidade dos custos ao preço do petróleo (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Integração com página Geopolítica (preço do petróleo)")
