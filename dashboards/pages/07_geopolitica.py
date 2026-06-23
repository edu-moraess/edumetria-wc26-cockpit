"""
dashboards/pages/07_geopolitica.py
Página 7 — Geopolítica
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Geopolítica e Risco Global", "Avaliação de risco sistêmico")


def load_indicator(indicator_code: str) -> pd.DataFrame:
    try:
        with get_connection() as conn:
            df = conn.execute("SELECT period, value FROM fact_indicator_values WHERE indicator_code = ? ORDER BY period", [indicator_code]).df()
        df["period"] = pd.to_datetime(df["period"])
        return df
    except Exception:
        return pd.DataFrame(columns=["period", "value"])


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

# KPIs
st.subheader("Métricas de Risco")
risk_kpis = []
for code, label, fmt in [("VIX", "VIX", "{:.2f}"), ("WTI_CRUDE", "WTI Crude", "${:.2f}"), ("BRENT_CRUDE", "Brent", "${:.2f}"), ("GOLD", "Ouro", "${:.2f}")]:
    df = load_indicator(code)
    if not df.empty:
        last, prev = df["value"].iloc[-1], df["value"].iloc[-2] if len(df) > 1 else df["value"].iloc[-1]
        delta = ((last / prev - 1) * 100) if prev else 0
        risk_kpis.append((label, fmt.format(last), f"{delta:+.2f}%"))
    else:
        risk_kpis.append((label, "—", None))
kpi_row(risk_kpis)

# VIX
st.subheader("VIX — Volatilidade Implícita")
df = load_indicator("VIX")
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name="VIX", line=dict(color="#FF4560")))
    fig.add_hline(y=20, line_dash="dash", line_color="#FFB300")
    fig.add_hline(y=30, line_dash="dash", line_color="#FF4560")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⏳ Dados VIX não disponíveis")

# Risk Score
st.subheader("World Cup Risk Score 2.0")
try:
    from models.montecarlo.risk_score_v2 import RiskScoreV2
    risk_engine = RiskScoreV2()
    risk_score = risk_engine.calculate()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score Total", f"{risk_score.total:.1f}")
    col2.metric("Financeiro", f"{risk_score.financial:.1f}")
    col3.metric("Energético", f"{risk_score.energy:.1f}")
    col4.metric("Macro", f"{risk_score.macro:.1f}")
except Exception as e:
    st.error(f"Erro ao calcular Risk Score: {e}")

st.subheader("Análise Geopolítica")
with st.expander("🇺🇸 Estados Unidos", expanded=True):
    st.markdown("- Ameaça terrorista: Baixa-moderada\n- Tensão com México: Moderada\n- Risco cibernético: Alto")
with st.expander("🇨🇦 Canadá"):
    st.markdown("- Ameaça terrorista: Baixa\n- Tensão com EUA: Baixa-moderada")
with st.expander("🇲🇽 México"):
    st.markdown("- Ameaça terrorista: Moderada\n- Tensão com EUA: Moderada-alta")
