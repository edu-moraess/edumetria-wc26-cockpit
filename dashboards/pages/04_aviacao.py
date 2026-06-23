"""
dashboards/pages/04_aviacao.py
Página 4 — Aviação
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

page_header("Aviação", "Métricas do setor aéreo e ETFs")


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

st.subheader("ETF Aviação (JETS)")
df = load_indicator("ETF_AVIATION")
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name="JETS", line=dict(color="#4C8BF5")))
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⏳ Dados de aviação não disponíveis")

st.subheader("Contexto Copa 2026")
st.markdown("""
- **17 aeroportos** sedes nos 3 países
- **Capacidade adicional**: ~2.000 voos/dia durante o evento
- **ETF JETS**: proxy do setor aéreo global
""")
