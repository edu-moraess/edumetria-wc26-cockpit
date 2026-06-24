import streamlit as st
import plotly.graph_objects as go
from dashboards.components import page_header, apply_theme
from utils.data_loader import load_indicator
from models.montecarlo.recession_monitor import calculate_recession_monitor

page_header("Recession Monitor", "Probabilidade de recessão nos EUA — 5 indicadores compostos")

result = calculate_recession_monitor()

if result["recession_score"] is not None:
    cols = st.columns(3)
    with cols[0]:
        st.metric("Recession Score", f"{result['recession_score']:.1f}", result["classification"])
    with cols[1]:
        st.metric("Completeness", f"{result['completeness_pct']:.0f}%")
    with cols[2]:
        status = "🟢 Baixo" if result["recession_score"] < 15 else ("🟡 Moderado" if result["recession_score"] < 35 else ("🟠 Elevado" if result["recession_score"] < 60 else "🔴 Crítico"))
        st.metric("Status", status)
    
    st.markdown("---")
    st.markdown("### Componentes")
    for name, comp in result["components"].items():
        prob = comp["data"]["prob"]
        sig = comp["data"].get("signal", "—")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"**{name}**")
            st.markdown(f"{prob:.1f}%" if prob is not None else "—")
        with col2:
            st.markdown(f"*{sig}*")
            st.markdown(f"Peso: {comp['weight']*100:.0f}%")
        st.markdown("---")
else:
    st.info("Recession Monitor indisponível — dados insuficientes.")

st.markdown("### Yield Spreads — Visual")
y10y2 = load_indicator("YIELD_SPREAD_10Y2Y", "USA")
if not y10y2.empty:
    fig = go.Figure(go.Scatter(x=y10y2["period"], y=y10y2["value"], mode="lines", name="10Y-2Y"))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.update_layout(title="Yield Spread 10Y-2Y (%)", xaxis_title="Data")
    apply_theme(fig)
    st.plotly_chart(fig)
