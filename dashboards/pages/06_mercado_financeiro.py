"""
dashboards/pages/06_mercado_financeiro.py
Página 6 — Mercado Financeiro
Índices, Setores, Drawdown, Correlação, Volatilidade — dados reais via yfinance.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Mercado Financeiro", "Índices · Setores · Drawdown · Correlação · Volatilidade")


@st.cache_data(ttl=3600)
def load_indicator(indicator_code: str) -> pd.DataFrame:
    """
    Carrega série de um indicador do banco.
    Deduplicação por período (keep='last') evita ValueError no pd.DataFrame
    quando há datas duplicadas — causado por múltiplas cargas do pipeline.
    """
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

    if df.empty:
        return pd.DataFrame(columns=["period", "value"])

    df["period"] = pd.to_datetime(df["period"])

    # Deduplicação — mantém último valor por data
    df = df.drop_duplicates(subset=["period"], keep="last")
    df = df.sort_values("period").reset_index(drop=True)

    return df


INDICATORS = {
    "SP500":                        "S&P 500 (EUA)",
    "TSX":                          "TSX Composite (Canadá)",
    "IPC_MEXICO":                   "IPC México",
    "VIX":                          "VIX",
    "WTI_CRUDE":                    "Petróleo WTI",
    "BRENT_CRUDE":                  "Petróleo Brent",
    "ETF_AVIATION":                 "ETF Aviação (JETS)",
    "ETF_LEISURE":                  "ETF Lazer/Entretenimento (PEJ)",
    "ETF_CONSUMER_DISCRETIONARY":   "ETF Consumo Discricionário (XLY)",
}

# ------------------------------------------------------------------
# KPIs — últimos valores disponíveis
# ------------------------------------------------------------------
kpi_items = []
for code, label in [
    ("SP500",       "S&P 500"),
    ("VIX",         "VIX"),
    ("WTI_CRUDE",   "WTI (US$/bbl)"),
    ("BRENT_CRUDE", "Brent (US$/bbl)"),
]:
    df = load_indicator(code)
    if not df.empty:
        last  = df["value"].iloc[-1]
        prev  = df["value"].iloc[-2] if len(df) > 1 else last
        delta = (last / prev - 1) * 100 if prev else 0
        kpi_items.append((label, f"{last:,.2f}", f"{delta:+.2f}%"))
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

# ------------------------------------------------------------------
# ABA 1 — ÍNDICES NACIONAIS
# ------------------------------------------------------------------
with tabs[0]:
    st.subheader("Índices Nacionais — base 100")
    fig = go.Figure()
    colors = ["#4C8BF5", "#00C8FF", "#00D4AA"]
    has_data = False
    for code, color in zip(["SP500", "TSX", "IPC_MEXICO"], colors):
        df = load_indicator(code)
        if not df.empty:
            normalized = df["value"] / df["value"].iloc[0] * 100
            fig.add_trace(go.Scatter(
                x=df["period"], y=normalized, mode="lines",
                name=INDICATORS[code], line=dict(color=color, width=1.5),
            ))
            has_data = True
    fig.update_layout(title="Índices nacionais (base 100 = início da série)")
    apply_theme(fig)
    if has_data:
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Índices nacionais — sem dados carregados")

# ------------------------------------------------------------------
# ABA 2 — ETFs SETORIAIS
# ------------------------------------------------------------------
with tabs[1]:
    st.subheader("ETFs Setoriais — Copa 2026 Watch List")
    fig = go.Figure()
    colors = ["#4C8BF5", "#00C8FF", "#FFB300"]
    has_data = False
    for code, color in zip(
        ["ETF_AVIATION", "ETF_LEISURE", "ETF_CONSUMER_DISCRETIONARY"], colors
    ):
        df = load_indicator(code)
        if not df.empty:
            normalized = df["value"] / df["value"].iloc[0] * 100
            fig.add_trace(go.Scatter(
                x=df["period"], y=normalized, mode="lines",
                name=INDICATORS[code], line=dict(color=color, width=1.5),
            ))
            has_data = True
    fig.update_layout(title="ETFs setoriais (base 100 = início da série)")
    apply_theme(fig)
    if has_data:
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("ETFs setoriais — sem dados carregados")

# ------------------------------------------------------------------
# ABA 3 — DRAWDOWN
# ------------------------------------------------------------------
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
        dd = compute_drawdown(df.set_index("period")["value"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dd.index, y=dd.values, mode="lines",
            fill="tozeroy", fillcolor="rgba(255,69,96,0.15)",
            line=dict(color="#FF4560", width=1.2),
            name="Drawdown (%)",
        ))
        fig.update_layout(
            title=f"Drawdown — {INDICATORS[indicator_select]}",
            yaxis_title="Drawdown (%)",
        )
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        max_dd      = dd.min()
        max_dd_date = dd.idxmin()
        st.caption(
            f"Maior drawdown: {max_dd:.1f}% em {max_dd_date.strftime('%b/%Y')}"
        )
    else:
        data_pending_notice(f"Drawdown — sem dados para {INDICATORS[indicator_select]}")

# ------------------------------------------------------------------
# ABA 4 — CORRELAÇÃO
# ------------------------------------------------------------------
with tabs[3]:
    st.subheader("Correlação entre Índices (janela selecionável)")

    window = st.slider("Janela de correlação (dias)", 30, 252, 90, step=30)

    codes_corr = ["SP500", "TSX", "IPC_MEXICO", "ETF_AVIATION", "WTI_CRUDE", "VIX"]
    series_dict = {}

    for code in codes_corr:
        df = load_indicator(code)
        if not df.empty:
            # Deduplicação já foi feita no load, mas garante index único
            s = df.set_index("period")["value"]
            s = s[~s.index.duplicated(keep="last")]
            series_dict[INDICATORS[code]] = s

    if len(series_dict) >= 2:
        # Alinha todas as séries no mesmo índice diário
        combined = pd.DataFrame(series_dict)
        combined = combined.sort_index()
        combined = combined[~combined.index.duplicated(keep="last")]

        returns = combined.pct_change().dropna(how="all")

        if len(returns) >= window:
            corr_matrix = returns.iloc[-window:].corr()

            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns.tolist(),
                y=corr_matrix.columns.tolist(),
                colorscale=[
                    [0.0,  "#FF4560"],
                    [0.5,  "#111827"],
                    [1.0,  "#4C8BF5"],
                ],
                zmid=0, zmin=-1, zmax=1,
                text=corr_matrix.round(2).values,
                texttemplate="%{text}",
                textfont={"size": 10},
            ))
            fig.update_layout(
                title=f"Correlação de retornos — últimos {window} dias",
            )
            apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            data_pending_notice(
                f"Correlação — dados insuficientes para janela de {window} dias "
                f"({len(returns)} observações disponíveis)"
            )
    else:
        data_pending_notice("Correlação — pelo menos 2 séries são necessárias")

# ------------------------------------------------------------------
# ABA 5 — VOLATILIDADE
# ------------------------------------------------------------------
with tabs[4]:
    st.subheader("Volatilidade Realizada (Rolling 21 dias, anualizada)")

    vol_select = st.selectbox(
        "Índice / ETF",
        ["SP500", "TSX", "IPC_MEXICO", "VIX", "WTI_CRUDE"],
        format_func=lambda c: INDICATORS.get(c, c),
        key="vol_select",
    )

    df = load_indicator(vol_select)

    if not df.empty:
        returns = df.set_index("period")["value"].pct_change().dropna()
        vol = returns.rolling(21).std() * np.sqrt(252) * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=vol.index, y=vol.values, mode="lines",
            line=dict(color="#4C8BF5", width=1.2),
            name="Vol. realizada 21d (anualizada %)",
        ))
        fig.update_layout(
            title=f"Volatilidade realizada anualizada — {INDICATORS[vol_select]}",
            yaxis_title="Vol. (%)",
        )
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        last_vol = vol.dropna().iloc[-1] if not vol.dropna().empty else None
        if last_vol is not None:
            st.caption(f"Volatilidade mais recente: {last_vol:.1f}% a.a.")
    else:
        data_pending_notice(f"Volatilidade — sem dados para {INDICATORS[vol_select]}")

st.markdown("###")
data_pending_notice(
    "Event Study (CAR por setor) — depende de modelagem em models/econometric/"
) 