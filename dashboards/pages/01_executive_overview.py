import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dashboards.components import page_header, apply_theme
from utils.data_loader import load_indicator, load_latest_value
from models.montecarlo.wcli_calculator import calculate_wcli

page_header("Executive Overview", "FIFA World Cup 2026™ — Impact Analytics Snapshot")

cols = st.columns(4)
with cols[0]:
    sp500 = load_latest_value("SP500", "USA")
    st.metric("S&P 500", f"{sp500:,.0f}" if sp500 else "—")
with cols[1]:
    vix = load_latest_value("VIX", "USA")
    st.metric("VIX", f"{vix:.1f}" if vix else "—")
with cols[2]:
    wti = load_latest_value("WTI_CRUDE", "USA")
    st.metric("WTI Crude", f"${wti:.1f}" if wti else "—")
with cols[3]:
    tsx = load_latest_value("TSX", "CAN")
    st.metric("TSX", f"{tsx:,.0f}" if tsx else "—")

st.markdown("---")

st.markdown("### World Cup Legacy Index (WCLI)")
wcli_data = []
for country in ["USA", "CAN", "MEX"]:
    result = calculate_wcli(country)
    wcli_data.append({
        "País": country,
        "WCLI": result["wcli_total"],
        "Classificação": result["classification"],
        "Completeness": f"{result['completeness_pct']:.0f}%"
    })
st.dataframe(pd.DataFrame(wcli_data), hide_index=True)

st.markdown("### Turismo — Chegadas Internacionais")
can = load_indicator("TOURISM_ARRIVALS", "CAN")
mex = load_indicator("TOURISM_ARRIVALS", "MEX")
fig = go.Figure()
if not can.empty:
    fig.add_trace(go.Scatter(x=can["period"], y=can["value"]/1e6, name="Canadá", mode="lines"))
if not mex.empty:
    fig.add_trace(go.Scatter(x=mex["period"], y=mex["value"]/1e6, name="México", mode="lines"))
fig.update_layout(title="Chegadas Internacionais (milhões)", xaxis_title="Ano", yaxis_title="Milhões")
apply_theme(fig)
st.plotly_chart(fig)

with st.expander("📊 FIFA Baseline (referência)"):
    from config import FIFA_BASELINE
    st.json(FIFA_BASELINE)
