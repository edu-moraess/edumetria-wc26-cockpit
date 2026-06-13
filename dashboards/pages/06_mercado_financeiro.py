"""
dashboards/pages/06_mercado_financeiro.py
Página 6 — Mercado Financeiro
Índices, Setores, Volatilidade — dados reais via yfinance (fact_indicator_values).
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Mercado Financeiro", "Índices · Setores · Volatilidade (dados reais via yfinance)")


@st.cache_data(ttl=600)
def load_indicator(indicator_code: str) -> pd.DataFrame:
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value
            FROM fact_indicator_values
            WHERE indicator_code = ?
            ORDER BY period
            """,
            [indicator_code],
        ).df()
    df["period"] = pd.to_datetime(df["period"])
    return df


INDICATORS = {
    "SP500": "S&P 500 (EUA)",
    "TSX": "TSX Composite (Canadá)",
    "IPC_MEXICO": "IPC México",
    "VIX": "VIX — Volatilidade",
    "WTI_CRUDE": "Petróleo WTI",
    "BRENT_CRUDE": "Petróleo Brent",
    "ETF_AVIATION": "ETF Aviação (JETS)",
    "ETF_LEISURE": "ETF Lazer/Entretenimento (PEJ)",
    "ETF_CONSUMER_DISCRETIONARY": "ETF Consumo Discricionário (XLY)",
}

# ------------------------------------------------------------------
# KPIs — últimos valores disponíveis
# ------------------------------------------------------------------
kpi_items = []
for code, label in [("SP500", "S&P 500"), ("VIX", "VIX"), ("WTI_CRUDE", "WTI (US$/bbl)"), ("BRENT_CRUDE", "Brent (US$/bbl)")]:
    df = load_indicator(code)
    if not df.empty:
        last_val = df["value"].iloc[-1]
        kpi_items.append((label, f"{last_val:,.2f}", None))
    else:
        kpi_items.append((label, "—", None))

kpi_row(kpi_items)

st.markdown("###")

tabs = st.tabs(["Índices Nacionais", "Petróleo & VIX", "ETFs Setoriais"])

with tabs[0]:
    st.subheader("Índices Nacionais — EUA, Canadá, México")
    fig = go.Figure()
    for code in ["SP500", "TSX", "IPC_MEXICO"]:
        df = load_indicator(code)
        if not df.empty:
            # normaliza para base 100 no início da série, para comparar escalas diferentes
            normalized = df["value"] / df["value"].iloc[0] * 100
            fig.add_trace(go.Scatter(x=df["period"], y=normalized, mode="lines", name=INDICATORS[code]))
    fig.update_layout(title="Índices nacionais (base 100 = início da série)")
    apply_theme(fig)
    if fig.data:
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Índices nacionais — aguardando dados")

with tabs[1]:
    st.subheader("Petróleo (WTI/Brent) e VIX")
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        for code in ["WTI_CRUDE", "BRENT_CRUDE"]:
            df = load_indicator(code)
            if not df.empty:
                fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=INDICATORS[code]))
        fig.update_layout(title="Preço do petróleo (US$/bbl)")
        apply_theme(fig)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            data_pending_notice("Petróleo — aguardando dados")

    with col2:
        df = load_indicator("VIX")
        fig = go.Figure()
        if not df.empty:
            fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name="VIX", line=dict(color="#E5534B")))
        fig.update_layout(title="VIX — Índice de Volatilidade")
        apply_theme(fig)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            data_pending_notice("VIX — aguardando dados")

with tabs[2]:
    st.subheader("ETFs Setoriais — Aviação, Lazer, Consumo Discricionário")
    fig = go.Figure()
    for code in ["ETF_AVIATION", "ETF_LEISURE", "ETF_CONSUMER_DISCRETIONARY"]:
        df = load_indicator(code)
        if not df.empty:
            normalized = df["value"] / df["value"].iloc[0] * 100
            fig.add_trace(go.Scatter(x=df["period"], y=normalized, mode="lines", name=INDICATORS[code]))
    fig.update_layout(title="ETFs setoriais (base 100 = início da série)")
    apply_theme(fig)
    if fig.data:
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("ETFs setoriais — aguardando dados")

st.markdown("###")
data_pending_notice("Event Study (CAR por setor) e GARCH-X — modelagem ainda pendente (models/econometric)")