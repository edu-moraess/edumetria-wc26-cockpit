"""
dashboards/pages/07_geopolitica.py
Página 7 — Geopolítica
Petróleo, VIX, Conflitos, Cadeias globais.
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402

page_header("Geopolítica e Cenários Estratégicos", "Petróleo · VIX · Conflitos · Cadeias Globais")

kpi_row([
    ("WTI/Brent (nível atual)*", "US$ —/bbl", None),
    ("VIX (nível atual)*", "—", None),
    ("GeoFactor Index*", "—", None),
    ("Regime Atual*", "—", None),
])

st.markdown("###")

st.caption(
    "Reaproveita a infraestrutura do Macro Geopolítico Model v4.0 "
    "(Ridge-VAR com Minnesota prior, GeoFactor Z-score, classificação "
    "dinâmica de regime, DCC) aplicada ao contexto específico da Copa 2026."
)

tabs = st.tabs(["Oriente Médio", "EUA-China", "Migração e Fronteiras", "Risco Sistêmico"])

with tabs[0]:
    st.subheader("Oriente Médio — Petróleo e Transporte Aéreo")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="WTI/Brent (US$/bbl)"))
    fig.update_layout(title="Preço do petróleo e custos operacionais (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Integração com modelo GARCH-X de commodities")

with tabs[1]:
    st.subheader("EUA-China — Comércio e Fluxos Turísticos")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Fluxo turístico China→América do Norte"], y=[None], name="Variação (%)"))
    fig.update_layout(title="Impacto de tensões comerciais sobre fluxos turísticos (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Cenários de comércio EUA-China x turismo")

with tabs[2]:
    st.subheader("Migração, Fronteiras e Segurança")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="Índice de restrição migratória"))
    fig.update_layout(title="Restrições migratórias — impacto em fluxo de visitantes (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Análise qualitativa + índice proprietário de restrição")

with tabs[3]:
    st.subheader("Risco Sistêmico e Confiança do Consumidor")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="VIX"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="GeoFactor Index"))
    fig.update_layout(title="VIX vs. GeoFactor Index (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Classificação dinâmica de regime via GeoFactor Z-score")
