"""
dashboards/pages/02_macroeconomia.py
Página 2 — Macroeconomia
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import HOST_COUNTRIES, COUNTRY_NAMES  # noqa: E402
from dashboards.components import page_header, apply_theme  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Macroeconomia", "Indicadores macroeconômicos — EUA, Canadá, México")


def load_indicator(indicator_code: str, country_code: str = None) -> pd.DataFrame:
    try:
        with get_connection() as conn:
            if country_code:
                df = conn.execute("SELECT period, value FROM fact_indicator_values WHERE indicator_code = ? AND country_code = ? ORDER BY period", [indicator_code, country_code]).df()
            else:
                df = conn.execute("SELECT period, value FROM fact_indicator_values WHERE indicator_code = ? ORDER BY period", [indicator_code]).df()
        df["period"] = pd.to_datetime(df["period"])
        return df
    except Exception:
        return pd.DataFrame(columns=["period", "value"])


# Verifica dados
has_data = False
try:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
        has_data = count > 0
except:
    pass

if not has_data:
    st.warning("⚠️ **Sem dados disponíveis**")
    st.info("Clique em **'🎲 Criar dados de demonstração'** na sidebar para visualizar esta página.")
    st.stop()

# ============ CONTEÚDO ============

country = st.selectbox("País", HOST_COUNTRIES, format_func=lambda c: COUNTRY_NAMES[c])

st.subheader("PIB e Inflação")
fig = go.Figure()

for code, label, color in [("GDP_NOMINAL", "PIB Nominal", "#4C8BF5"), ("CPI", "CPI (Inflação)", "#FF4560")]:
    df = load_indicator(code, country)
    if not df.empty:
        fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=label, line=dict(color=color)))

if fig.data:
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⏳ Dados macro não disponíveis para este país")

st.subheader("Desemprego e Taxa de Juros")
fig2 = go.Figure()

for code, label, color in [("UNEMPLOYMENT_RATE", "Desemprego (%)", "#00D4AA"), ("POLICY_RATE", "Taxa de Política Monetária", "#FFB300")]:
    df = load_indicator(code, country)
    if not df.empty:
        fig2.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=label, line=dict(color=color)))

if fig2.data:
    apply_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("⏳ Dados não disponíveis")

st.subheader("Yield Spreads")
fig3 = go.Figure()
for code, label, color in [("YIELD_SPREAD_10Y2Y", "10Y-2Y", "#4C8BF5"), ("YIELD_SPREAD_10Y3M", "10Y-3M", "#A78BFA")]:
    df = load_indicator(code, country)
    if not df.empty:
        fig3.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=label, line=dict(color=color)))
        fig3.add_hline(y=0, line_dash="dash", line_color="red")

if fig3.data:
    apply_theme(fig3)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("⏳ Dados de yield spreads não disponíveis")
