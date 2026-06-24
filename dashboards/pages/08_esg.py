import streamlit as st
import plotly.graph_objects as go
from dashboards.components import page_header, apply_theme
from utils.data_loader import load_indicator

page_header("ESG", "Environmental, Social, Governance — Métricas de sustentabilidade")

co2_usa = load_indicator("CO2_EMISSIONS", "USA")
co2_can = load_indicator("CO2_EMISSIONS", "CAN")
co2_mex = load_indicator("CO2_EMISSIONS", "MEX")
fig = go.Figure()
if not co2_usa.empty:
    fig.add_trace(go.Scatter(x=co2_usa["period"], y=co2_usa["value"], mode="lines", name="EUA"))
if not co2_can.empty:
    fig.add_trace(go.Scatter(x=co2_can["period"], y=co2_can["value"], mode="lines", name="Canadá"))
if not co2_mex.empty:
    fig.add_trace(go.Scatter(x=co2_mex["period"], y=co2_mex["value"], mode="lines", name="México"))
fig.update_layout(title="Emissões de CO₂ (milhões de toneladas)", xaxis_title="Data", yaxis_title="Mt CO₂")
apply_theme(fig)
st.plotly_chart(fig)

ren_usa = load_indicator("RENEWABLE_SHARE", "USA")
ren_can = load_indicator("RENEWABLE_SHARE", "CAN")
ren_mex = load_indicator("RENEWABLE_SHARE", "MEX")
fig = go.Figure()
if not ren_usa.empty:
    fig.add_trace(go.Scatter(x=ren_usa["period"], y=ren_usa["value"], mode="lines", name="EUA"))
if not ren_can.empty:
    fig.add_trace(go.Scatter(x=ren_can["period"], y=ren_can["value"], mode="lines", name="Canadá"))
if not ren_mex.empty:
    fig.add_trace(go.Scatter(x=ren_mex["period"], y=ren_mex["value"], mode="lines", name="México"))
fig.update_layout(title="Participação de Energia Renovável (%)", xaxis_title="Data", yaxis_title="%")
apply_theme(fig)
st.plotly_chart(fig)

energy = load_indicator("ENERGY_CONSUMPTION", "USA")
if not energy.empty:
    fig = go.Figure(go.Scatter(x=energy["period"], y=energy["value"], mode="lines", name="Consumo", line=dict(color="#FFB300")))
    fig.update_layout(title="Consumo de Energia (TWh)", xaxis_title="Data")
    apply_theme(fig)
    st.plotly_chart(fig)

st.markdown("---")
st.markdown("**FIFA 2026 Commitments:** Net-zero operations, 100% renewable energy in stadiums.")
