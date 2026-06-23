"""
dashboards/pages/03_turismo.py
Página 3 — Turismo
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import HOST_COUNTRIES, COUNTRY_NAMES  # noqa: E402
from dashboards.components import page_header, apply_theme  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Turismo", "Chegadas internacionais e impacto do evento")


def load_indicator(indicator_code: str, country_code: str) -> pd.DataFrame:
    try:
        with get_connection() as conn:
            df = conn.execute("SELECT period, value FROM fact_indicator_values WHERE indicator_code = ? AND country_code = ? ORDER BY period", [indicator_code, country_code]).df()
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

st.subheader("Chegadas de Turistas Internacionais")
fig = go.Figure()
has_tourism = False

for country_code, label, color in [("CAN", "Canadá", "#3FB68B"), ("MEX", "México", "#C9A227")]:
    df = load_indicator("TOURISM_ARRIVALS", country_code)
    if not df.empty:
        fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines+markers", name=label, line=dict(color=color)))
        has_tourism = True

if has_tourism:
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⏳ Dados de turismo não disponíveis")

st.subheader("Projeção de Impacto — Copa 2026")
st.markdown("""
**Baseline FIFA:**
- Visitantes totais estimados: **6.5 milhões**
- Distribuição: EUA (principal), Canadá, México
- Impacto econômico líquido: **US$ 40.9 bn**
""")
