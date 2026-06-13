"""
dashboards/pages/06_mercado_financeiro.py
Página 6 — Mercado Financeiro
Índices, Setores, Retornos, Volatilidade. Foco em retornos anormais
associados a megaeventos esportivos (event study).
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402

page_header("Mercado Financeiro", "Índices · Setores · Retornos Anormais · Volatilidade")

kpi_row([
    ("Retorno Anormal Médio (CAR)*", "—%", None),
    ("Volatilidade Implícita (var.)*", "—%", None),
    ("Setor de Maior Retorno*", "—", None),
    ("Janela de Event Study*", "[-30, +30] dias", None),
])

st.markdown("###")

st.caption(
    "Metodologia: Event Study (modelo de mercado / Fama-French) aplicado a "
    "índices setoriais de turismo, hotelaria, aviação, entretenimento, "
    "infraestrutura, tecnologia e mídia ao redor de datas-chave do evento "
    "(sorteio, abertura, semifinais, final)."
)

tabs = st.tabs(["Retornos Anormais por Setor", "Índices Gerais", "Volatilidade (VIX-like)"])

with tabs[0]:
    st.subheader("Cumulative Abnormal Returns (CAR) por setor")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Turismo", "Hotelaria", "Aviação", "Entretenimento", "Infraestrutura", "Tecnologia", "Mídia"],
        y=[None] * 7,
        name="CAR (%)",
    ))
    fig.update_layout(title="CAR por setor — janela de evento (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Event study com dados de mercado (yfinance / Bloomberg)")

with tabs[1]:
    st.subheader("Desempenho de índices de referência")
    fig = go.Figure()
    for idx in ["S&P 500", "TSX (Canadá)", "IPC (México)"]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name=idx))
    fig.update_layout(title="Índices nacionais — janela do evento (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Séries de índices via yfinance")

with tabs[2]:
    st.subheader("Volatilidade implícita / realizada")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="Volatilidade (GARCH)"))
    fig.update_layout(title="Volatilidade condicional — GARCH (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Modelo GARCH-X reaproveitado do macro model (models/econometric)")
