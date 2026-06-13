"""
dashboards/pages/03_turismo.py
Página 3 — Turismo
Visitantes, Gastos, Permanência, Fluxos.
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import FIFA_BASELINE, HOST_COUNTRIES, COUNTRY_NAMES  # noqa: E402
from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402

page_header("Turismo Internacional", "Visitantes · Gastos · Permanência · Fluxos")

kpi_row([
    ("Visitantes Totais (baseline FIFA)", f"{FIFA_BASELINE['global']['visitors_total']:,}", None),
    ("Visitantes Incrementais (estimado)*", "—", None),
    ("Permanência Média*", "— dias", None),
    ("Gasto Médio por Visitante*", "US$ —", None),
])

st.markdown("###")

country = st.selectbox("País", [COUNTRY_NAMES[c] for c in HOST_COUNTRIES])

tabs = st.tabs(["Fluxos por Origem", "Setores Beneficiados", "Elasticidade-Preço"])

with tabs[0]:
    st.subheader(f"Fluxos turísticos incrementais — {country}")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Europa", "América Latina", "Ásia", "América do Norte"],
                          y=[None, None, None, None], name="Visitantes incrementais"))
    fig.update_layout(title="Origem dos fluxos turísticos incrementais (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Dados de fluxo por origem (Tourism Economics / STR Global)")

with tabs[1]:
    st.subheader("Impacto setorial")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Hotelaria", "Aviação", "Restaurantes", "Varejo", "Entretenimento"],
        y=[None, None, None, None, None],
        name="Receita incremental (US$ bn)",
    ))
    fig.update_layout(title="Receita incremental por setor (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Decomposição setorial do gasto turístico")

with tabs[2]:
    st.subheader("Elasticidade-preço da demanda turística")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Elasticidade estimada"))
    fig.update_layout(title="Elasticidade-preço por segmento (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Estimação econométrica de elasticidade-preço")
