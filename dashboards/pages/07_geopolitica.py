import streamlit as st
import plotly.graph_objects as go
from dashboards.components import page_header, apply_theme
from utils.data_loader import load_indicator
from models.montecarlo.risk_score_v2 import calculate_risk_score_v2

page_header("Geopolítica", "Risk Score 2.0 · Commodities · Volatilidade")

result = calculate_risk_score_v2()
if result["risk_score"] is not None:
    cols = st.columns(2)
    with cols[0]:
        st.metric("Risk Score 2.0", f"{result['risk_score']:.1f}", result["classification"])
    with cols[1]:
        st.metric("Completeness", f"{result['completeness_pct']:.0f}%")
    st.markdown("#### Decomposição por dimensão")
    for dim_name, dim in result["dimensions"].items():
        score_str = f"{dim['score']:.1f}" if dim["score"] is not None else "—"
        st.markdown(f"**{dim['label']}**: {score_str} (completeness: {dim['completeness']:.0%})")
else:
    st.info("Risk Score 2.0 indisponível — dados insuficientes.")

st.markdown("### Commodities — Risco Geopolítico")
wti = load_indicator("WTI_CRUDE", "USA")
brent = load_indicator("BRENT_CRUDE", "USA")
ng = load_indicator("NATURAL_GAS", "USA")
fig = go.Figure()
if not wti.empty:
    fig.add_trace(go.Scatter(x=wti["period"], y=wti["value"], name="WTI", mode="lines"))
if not brent.empty:
    fig.add_trace(go.Scatter(x=brent["period"], y=brent["value"], name="Brent", mode="lines"))
if not ng.empty:
    fig.add_trace(go.Scatter(x=ng["period"], y=ng["value"], name="Gás Natural", mode="lines", yaxis="y2"))
fig.update_layout(title="Petróleo e Gás Natural", xaxis_title="Data", yaxis_title="Petróleo (US$/bbl)", yaxis2=dict(title="Gás Natural (US$/MMBtu)", overlaying="y", side="right"))
apply_theme(fig)
st.plotly_chart(fig)

vix = load_indicator("VIX", "USA")
if not vix.empty:
    fig = go.Figure(go.Scatter(x=vix["period"], y=vix["value"], mode="lines", name="VIX", line=dict(color="#FF4560")))
    fig.add_hline(y=20, line_dash="dash", line_color="gray")
    fig.update_layout(title="VIX — Risco de Mercado", xaxis_title="Data")
    apply_theme(fig)
    st.plotly_chart(fig)
