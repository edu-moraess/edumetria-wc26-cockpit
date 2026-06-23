"""
dashboards/pages/10_recession_monitor.py
Página 10 — Recession Monitor
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, apply_theme  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Recession Monitor", "Probabilidade de recessão nos EUA — indicadores antecedentes")

has_data = False
try:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
        has_data = count > 0
except:
    pass

if not has_data:
    st.warning("⚠️ **Sem dados disponíveis**")
    st.info("Clique em **'🎲 Criar dados de demonstração'** na sidebar.")
    st.stop()

from models.montecarlo.recession_monitor import calculate_recession_monitor  # noqa: E402

result = calculate_recession_monitor()

st.subheader("Score Composto de Recessão")
col1, col2, col3 = st.columns(3)
score = result["recession_score"] or 0
col1.metric("Probabilidade", f"{score:.1f}%")
col2.metric("Classificação", result["classification"])
col3.metric("Cobertura", f"{result['completeness_pct']:.0f}%")

# Barras de cada indicador
st.subheader("Indicadores Individualmente")
for name, comp in result["components"].items():
    prob = comp["data"]["prob"]
    sig = comp["data"].get("signal", "—")
    if prob is not None:
        st.progress(min(prob / 100, 1.0), text=f"{name}: {prob:.1f}% — {sig}")
    else:
        st.caption(f"{name}: sem dados")

# Yield spreads
st.subheader("Yield Spreads (preditor de recessão)")
fig = go.Figure()

try:
    with get_connection() as conn:
        df_10y2y = conn.execute("SELECT period, value FROM fact_indicator_values WHERE indicator_code = 'YIELD_SPREAD_10Y2Y' ORDER BY period").df()
        df_10y3m = conn.execute("SELECT period, value FROM fact_indicator_values WHERE indicator_code = 'YIELD_SPREAD_10Y3M' ORDER BY period").df()
    
    if not df_10y2y.empty:
        df_10y2y["period"] = pd.to_datetime(df_10y2y["period"])
        fig.add_trace(go.Scatter(x=df_10y2y["period"], y=df_10y2y["value"], mode="lines", name="10Y-2Y", line=dict(color="#4C8BF5")))
    
    if not df_10y3m.empty:
        df_10y3m["period"] = pd.to_datetime(df_10y3m["period"])
        fig.add_trace(go.Scatter(x=df_10y3m["period"], y=df_10y3m["value"], mode="lines", name="10Y-3M", line=dict(color="#A78BFA")))
    
    fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Inversão")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.info(f"⏳ Dados de yield spreads não disponíveis: {e}")

st.caption("Referências: Sahm (2019), Estrella & Mishkin (1998), Conference Board, Fed NY")
