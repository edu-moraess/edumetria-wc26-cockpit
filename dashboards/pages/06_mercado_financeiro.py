import streamlit as st
import plotly.graph_objects as go
from dashboards.components import page_header, apply_theme
from utils.data_loader import load_indicator

page_header("Mercado Financeiro", "Índices, commodities, ETFs e volatilidade")

indices = {"SP500": ("S&P 500", "#4C8BF5"), "NASDAQ": ("Nasdaq", "#00C8FF"), "TSX": ("TSX (CAN)", "#00D4AA"), "IPC_MEXICO": ("IPC (MEX)", "#FFB300")}
fig = go.Figure()
for code, (name, color) in indices.items():
    country = "CAN" if code == "TSX" else ("MEX" if code == "IPC_MEXICO" else "USA")
    df = load_indicator(code, country)
    if not df.empty:
        fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=name, line=dict(color=color)))
fig.update_layout(title="Índices de Mercado", xaxis_title="Data", yaxis_title="Pontos")
apply_theme(fig)
st.plotly_chart(fig)

st.markdown("### Commodities")
comm = {"WTI_CRUDE": ("WTI", "#4C8BF5"), "BRENT_CRUDE": ("Brent", "#00D4AA"), "GOLD": ("Ouro", "#FFB300"), "NATURAL_GAS": ("Gás Natural", "#A78BFA")}
fig = go.Figure()
for code, (name, color) in comm.items():
    df = load_indicator(code, "USA")
    if not df.empty:
        fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=name, line=dict(color=color)))
fig.update_layout(title="Commodities", xaxis_title="Data", yaxis_title="US$")
apply_theme(fig)
st.plotly_chart(fig)

vix = load_indicator("VIX", "USA")
if not vix.empty:
    fig = go.Figure(go.Scatter(x=vix["period"], y=vix["value"], mode="lines", name="VIX", line=dict(color="#FF4560")))
    fig.add_hline(y=20, line_dash="dash", line_color="gray", annotation_text="Média histórica")
    fig.update_layout(title="VIX — Índice de Volatilidade", xaxis_title="Data")
    apply_theme(fig)
    st.plotly_chart(fig)
