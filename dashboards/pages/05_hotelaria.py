import streamlit as st
import plotly.graph_objects as go
from dashboards.components import page_header, apply_theme
from utils.data_loader import load_indicator

page_header("Hotelaria", "Métricas do setor hoteleiro — ADR, ocupação, RevPAR")

adr = load_indicator("HOTEL_ADR", "USA")
if not adr.empty:
    fig = go.Figure(go.Scatter(x=adr["period"], y=adr["value"], mode="lines", name="ADR", line=dict(color="#4C8BF5")))
    fig.update_layout(title="ADR — Average Daily Rate (US$)", xaxis_title="Data", yaxis_title="US$")
    apply_theme(fig)
    st.plotly_chart(fig)

occ = load_indicator("HOTEL_OCCUPANCY", "USA")
if not occ.empty:
    fig = go.Figure(go.Scatter(x=occ["period"], y=occ["value"], mode="lines", name="Ocupação", line=dict(color="#00D4AA")))
    fig.update_layout(title="Taxa de Ocupação (%)", xaxis_title="Data", yaxis_title="%")
    apply_theme(fig)
    st.plotly_chart(fig)

rev = load_indicator("HOTEL_REVPAR", "USA")
if not rev.empty:
    fig = go.Figure(go.Scatter(x=rev["period"], y=rev["value"], mode="lines", name="RevPAR", line=dict(color="#FFB300")))
    fig.update_layout(title="RevPAR — Revenue per Available Room (US$)", xaxis_title="Data", yaxis_title="US$")
    apply_theme(fig)
    st.plotly_chart(fig)

st.markdown("### Ações de Redes Hoteleiras")
tickers = {"MAR": "Marriott", "HLT": "Hilton", "H": "Hyatt"}
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

st.markdown("---")
st.markdown("**Contexto FIFA 2026:** Projeção de 45,000 quartos de hotel necessários nos EUA.")
