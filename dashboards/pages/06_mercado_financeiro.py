"""
dashboards/pages/06_mercado_financeiro.py
Página 6 — Mercado Financeiro
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, apply_theme  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Mercado Financeiro", "Índices, ETFs e commodities")


def load_indicator(indicator_code: str) -> pd.DataFrame:
    try:
        with get_connection() as conn:
            df = conn.execute("SELECT period, value FROM fact_indicator_values WHERE indicator_code = ? ORDER BY period", [indicator_code]).df()
        df["period"] = pd.to_datetime(df["period"])
        return df
    except Exception:
        return pd.DataFrame(columns=["period", "value"])


has_data = False
try:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
        has_data = count > 0
except:
    pass

if not has_data:
    st.warning("⚠️ **Sem dados disponíveis**")
    st.info("Clique em **'🎲 Criar dados de demonstração'** na sidebar.")
    st.stop()

st.subheader("Índices Principais")
fig = go.Figure()
has_data_chart = False

for code, label, color in [
    ("SP500", "S&P 500", "#4C8BF5"),
    ("NASDAQ", "Nasdaq", "#00C8FF"),
    ("TSX", "TSX (CAN)", "#3FB68B"),
    ("IPC_MEXICO", "IPC (MEX)", "#C9A227"),
]:
    df = load_indicator(code)
    if not df.empty:
        fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=label, line=dict(color=color)))
        has_data_chart = True

if has_data_chart:
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⏳ Dados de mercado não disponíveis")

st.subheader("Commodities")
fig2 = go.Figure()
has_commodities = False

for code, label, color in [
    ("WTI_CRUDE", "WTI Crude", "#4C8BF5"),
    ("BRENT_CRUDE", "Brent Crude", "#00C8FF"),
    ("GOLD", "Ouro", "#FFB300"),
]:
    df = load_indicator(code)
    if not df.empty:
        fig2.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=label, line=dict(color=color)))
        has_commodities = True

if has_commodities:
    apply_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("⏳ Dados de commodities não disponíveis")
