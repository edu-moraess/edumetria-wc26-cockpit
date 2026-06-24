import streamlit as st
import plotly.graph_objects as go
from dashboards.components import page_header, apply_theme
from utils.data_loader import load_indicator

page_header("Macroeconomia", "Indicadores macroeconômicos EUA · Canadá · México")

country = st.selectbox("País", ["USA", "CAN", "MEX"], index=0)

gdp = load_indicator("GDP_NOMINAL", country)
if not gdp.empty:
    fig = go.Figure(go.Scatter(x=gdp["period"], y=gdp["value"], mode="lines+markers", name="PIB Nominal"))
    fig.update_layout(title="PIB Nominal", xaxis_title="Data", yaxis_title="US$ bn")
    apply_theme(fig)
    st.plotly_chart(fig)
else:
    st.info("Dados de PIB não disponíveis.")

col1, col2 = st.columns(2)
with col1:
    cpi = load_indicator("CPI", country)
    if not cpi.empty:
        fig = go.Figure(go.Scatter(x=cpi["period"], y=cpi["value"], mode="lines", name="CPI", line=dict(color="#4C8BF5")))
        fig.update_layout(title="CPI — Índice de Preços", xaxis_title="Data")
        apply_theme(fig)
        st.plotly_chart(fig)
with col2:
    unemp = load_indicator("UNEMPLOYMENT_RATE", country)
    if not unemp.empty:
        fig = go.Figure(go.Scatter(x=unemp["period"], y=unemp["value"], mode="lines", name="Desemprego", line=dict(color="#FF4560")))
        fig.update_layout(title="Taxa de Desemprego (%)", xaxis_title="Data")
        apply_theme(fig)
        st.plotly_chart(fig)

if country == "USA":
    st.markdown("### Yield Curve Spreads")
    y10y2 = load_indicator("YIELD_SPREAD_10Y2Y", "USA")
    y10y3 = load_indicator("YIELD_SPREAD_10Y3M", "USA")
    fig = go.Figure()
    if not y10y2.empty:
        fig.add_trace(go.Scatter(x=y10y2["period"], y=y10y2["value"], name="10Y-2Y", mode="lines"))
    if not y10y3.empty:
        fig.add_trace(go.Scatter(x=y10y3["period"], y=y10y3["value"], name="10Y-3M", mode="lines"))
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(title="Yield Spreads (%)", xaxis_title="Data", yaxis_title="Spread (%)")
    apply_theme(fig)
    st.plotly_chart(fig)
