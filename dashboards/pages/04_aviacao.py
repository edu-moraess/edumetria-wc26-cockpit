import streamlit as st
import plotly.graph_objects as go
from dashboards.components import page_header, apply_theme
from utils.data_loader import load_indicator

page_header("Aviação", "Métricas do setor aéreo — tráfego, combustível, ações")

air = load_indicator("AIR_TRAFFIC_TSA", "USA")
if not air.empty:
    fig = go.Figure(go.Scatter(x=air["period"], y=air["value"], mode="lines", name="Tráfego Aéreo (TSA proxy)", line=dict(color="#4C8BF5")))
    fig.update_layout(title="Tráfego Aéreo — Passageiros (milhões)", xaxis_title="Data", yaxis_title="Milhões")
    apply_theme(fig)
    st.plotly_chart(fig)
else:
    st.info("Dados de tráfego aéreo não disponíveis.")

jf = load_indicator("JET_FUEL_PRICE", "USA")
if not jf.empty:
    fig = go.Figure(go.Scatter(x=jf["period"], y=jf["value"], mode="lines", name="Jet Fuel", line=dict(color="#FFB300")))
    fig.update_layout(title="Preço do Jet Fuel (US$/galão)", xaxis_title="Data")
    apply_theme(fig)
    st.plotly_chart(fig)

st.markdown("### Ações de Companhias Aéreas")
tickers = {"LUV": "Southwest Airlines", "DAL": "Delta Air Lines", "UAL": "United Airlines", "AAL": "American Airlines"}
fig = go.Figure()
for code, name in tickers.items():
    df = load_indicator(code, "USA")
    if not df.empty:
        fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=name))
if fig.data:
    fig.update_layout(title="Preço das Ações (US$)", xaxis_title="Data", yaxis_title="US$")
    apply_theme(fig)
    st.plotly_chart(fig)
else:
    st.info("Dados de ações não disponíveis.")

jet = load_indicator("ETF_AVIATION", "USA")
if not jet.empty:
    fig = go.Figure(go.Scatter(x=jet["period"], y=jet["value"], mode="lines", name="JETS ETF", line=dict(color="#00D4AA")))
    fig.update_layout(title="ETF Setor Aviação (JETS)", xaxis_title="Data", yaxis_title="US$")
    apply_theme(fig)
    st.plotly_chart(fig)
