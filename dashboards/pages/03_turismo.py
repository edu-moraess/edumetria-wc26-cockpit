import streamlit as st
import plotly.graph_objects as go
from dashboards.components import page_header, apply_theme
from utils.data_loader import load_indicator

page_header("Turismo", "Chegadas internacionais — Canadá e México")

can = load_indicator("TOURISM_ARRIVALS", "CAN")
mex = load_indicator("TOURISM_ARRIVALS", "MEX")

fig = go.Figure()
if not can.empty:
    fig.add_trace(go.Scatter(x=can["period"], y=can["value"]/1e6, name="Canadá", mode="lines", line=dict(color="#4C8BF5")))
if not mex.empty:
    fig.add_trace(go.Scatter(x=mex["period"], y=mex["value"]/1e6, name="México", mode="lines", line=dict(color="#00D4AA")))
fig.update_layout(title="Chegadas de Turistas Internacionais (milhões)", xaxis_title="Data", yaxis_title="Milhões de visitantes")
apply_theme(fig)
st.plotly_chart(fig)

cols = st.columns(2)
with cols[0]:
    if not can.empty:
        latest_can = can.iloc[-1]["value"] / 1e6
        prev_can = can.iloc[-13]["value"] / 1e6 if len(can) >= 13 else can.iloc[0]["value"] / 1e6
        delta_can = ((latest_can / prev_can) - 1) * 100 if prev_can > 0 else 0
        st.metric("Canadá (último mês)", f"{latest_can:.2f}M", f"{delta_can:+.1f}%")
    else:
        st.metric("Canadá", "—")
with cols[1]:
    if not mex.empty:
        latest_mex = mex.iloc[-1]["value"] / 1e6
        prev_mex = mex.iloc[-13]["value"] / 1e6 if len(mex) >= 13 else mex.iloc[0]["value"] / 1e6
        delta_mex = ((latest_mex / prev_mex) - 1) * 100 if prev_mex > 0 else 0
        st.metric("México (último mês)", f"{latest_mex:.2f}M", f"{delta_mex:+.1f}%")
    else:
        st.metric("México", "—")

st.markdown("---")
st.markdown("**Contexto FIFA 2026:** Projeção de 6.5 milhões de visitantes no total.")
