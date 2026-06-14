"""
dashboards/pages/06_mercado_financeiro.py
Página 6 — Mercado Financeiro
Índices, Setores, Volatilidade, Drawdown, Correlação — dados reais via yfinance.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Mercado Financeiro", "Índices · Setores · Drawdown · Correlação · Volatilidade")


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
    "VIX": "VIX",
    "WTI_CRUDE": "Petróleo WTI",
    "BRENT_CRUDE": "Petróleo Brent",
    "ETF_AVIATION": "ETF Aviação (JETS)",
    "ETF_LEISURE": "ETF Lazer/Entretenimento (PEJ)",
    "ETF_CONSUMER_DISCRETIONARY": "ETF Consumo Discricionário (XLY)",
}

# ------------------------------------------------------------------
# KPIs
# ------------------------------------------------------------------
kpi_items = []
for code, label in [("SP500", "S&P 500"), ("VIX", "VIX"),
                     ("WTI_CRUDE", "WTI (US$/bbl)"), ("BRENT_CRUDE", "Brent (US$/bbl)")]:
    df = load_indicator(code)
    if not df.empty:
        last = df["value"].iloc[-1]
        prev = df["value"].iloc[-2] if len(df) > 1 else last
        delta_pct = (last / prev - 1) * 100 if prev else 0
        kpi_items.append((label, f"{last:,.2f}", f"{delta_pct:+.2f}%"))
    else:
        kpi_items.append((label, "—", None))

kpi_row(kpi_items)

st.markdown("###")

tabs = st.tabs([
    "Índices Nacionais",
    "ETFs Setoriais",
    "Drawdown Analysis",
    "Correlação",
    "Volatilidade",
])

with tabs[0]:
    st.subheader("Índices Nacionais — EUA, Canadá, México (base 100)")
    fig = go.Figure()
    for code in ["SP500", "TSX", "IPC_MEXICO"]:
        df = load_indicator(code)
        if not df.empty:
            normalized = df["value"] / df["value"].iloc[0] * 100
            fig.add_trace(go.Scatter(x=df["period"], y=normalized, mode="lines", name=INDICATORS[code]))
    fig.update_layout(title="Índices nacionais (base 100 = início da série)")
    apply_theme(fig)
    if fig.data:
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Índices — sem dados carregados")

with tabs[1]:
    st.subheader("ETFs Setoriais — Copa 2026 Watch List")
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
        data_pending_notice("ETFs setoriais — sem dados carregados")

with tabs[2]:
    st.subheader("Drawdown Analysis — Máxima Queda por Índice")

    def compute_drawdown(series: pd.Series) -> pd.Series:
        rolling_max = series.cummax()
        return (series - rolling_max) / rolling_max * 100

    indicator_select = st.selectbox(
        "Índice / ETF",
        ["SP500", "TSX", "IPC_MEXICO", "ETF_AVIATION", "ETF_LEISURE"],
        format_func=lambda c: INDICATORS.get(c, c),
        key="drawdown_select",
    )

    df = load_indicator(indicator_select)
    if not df.empty:
        drawdown = compute_drawdown(df.set_index("period")["value"])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=drawdown.index, y=drawdown.values, mode="lines",
            fill="tozeroy", fillcolor="rgba(229,83,75,0.2)",
            line=dict(color="#E5534B"),
            name="Drawdown (%)",
        ))
        fig.update_layout(
            title=f"Drawdown — {INDICATORS[indicator_select]}",
            yaxis_title="Drawdown (%)",
        )
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        max_dd = drawdown.min()
        max_dd_date = drawdown.idxmin()
        st.caption(f"Maior drawdown: {max_dd:.1f}% em {max_dd_date.strftime('%b/%Y')}")
    else:
        data_pending_notice("Drawdown — sem dados carregados")

with tabs[3]:
    st.subheader("Correlação entre Índices (janela selecionável)")

    window = st.slider("Janela de correlação (dias)", 30, 252, 90, step=30)

    codes_corr = ["SP500", "TSX", "IPC_MEXICO", "ETF_AVIATION", "WTI_CRUDE", "VIX"]
    dfs = {}
    for code in codes_corr:
        df = load_indicator(code)
        if not df.empty:
            dfs[INDICATORS[code]] = df.set_index("period")["value"]

    if len(dfs) >= 2:
        combined = pd.DataFrame(dfs).dropna()
        returns = combined.pct_change().dropna()

        if len(returns) >= window:
            rolling_corr = returns.iloc[-window:].corr()

            fig = go.Figure(data=go.Heatmap(
                z=rolling_corr.values,
                x=rolling_corr.columns.tolist(),
                y=rolling_corr.columns.tolist(),
                colorscale="RdBu",
                zmid=0,
                zmin=-1, zmax=1,
                text=rolling_corr.round(2).values,
                texttemplate="%{text}",
            ))
            fig.update_layout(title=f"Correlação de retornos ({window} dias)")
            apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            data_pending_notice("Correlação — dados insuficientes para a janela selecionada")
    else:
        data_pending_notice("Correlação — pelo menos 2 séries são necessárias")

with tabs[4]:
    st.subheader("Volatilidade Realizada (Rolling 21 dias)")

    vol_select = st.selectbox(
        "Índice / ETF",
        ["SP500", "TSX", "IPC_MEXICO", "VIX", "WTI_CRUDE"],
        format_func=lambda c: INDICATORS.get(c, c),
        key="vol_select",
    )

    df = load_indicator(vol_select)
    if not df.empty:
        returns = df.set_index("period")["value"].pct_change().dropna()
        vol = returns.rolling(21).std() * np.sqrt(252) * 100  # anualizada

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=vol.index, y=vol.values, mode="lines",
            line=dict(color="#C9A227"),
            name="Vol. realizada 21d (anualizada %)",
        ))
        fig.update_layout(
            title=f"Volatilidade realizada anualizada — {INDICATORS[vol_select]}",
            yaxis_title="Vol. (%)",
        )
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        last_vol = vol.dropna().iloc[-1]
        st.caption(f"Volatilidade mais recente: {last_vol:.1f}% a.a.")
    else:
        data_pending_notice("Volatilidade — sem dados carregados")

st.markdown("###")
data_pending_notice("Event Study (CAR por setor) — depende de modelagem em models/econometric/")