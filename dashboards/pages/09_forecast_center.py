"""
dashboards/pages/09_forecast_center.py
Página 9 — Forecast Center
PIB, Emprego, Turismo, FDI, Receita Fiscal, Consumo — horizonte 2026-2035,
com distribuições Monte Carlo e seleção de cenário.
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import (  # noqa: E402
    HOST_COUNTRIES, COUNTRY_NAMES, SCENARIOS,
    FORECAST_START_YEAR, FORECAST_END_YEAR, MONTE_CARLO_N_SIMULATIONS,
)
from dashboards.components import page_header, apply_theme, data_pending_notice  # noqa: E402

page_header(
    "Forecast Center",
    f"Projeções {FORECAST_START_YEAR}-{FORECAST_END_YEAR} · "
    f"Monte Carlo ({MONTE_CARLO_N_SIMULATIONS:,} simulações) · "
    f"XGBoost · LightGBM · Prophet · LSTM",
)

col1, col2, col3 = st.columns(3)
with col1:
    country = st.selectbox("País", [COUNTRY_NAMES[c] for c in HOST_COUNTRIES])
with col2:
    indicator = st.selectbox(
        "Indicador",
        ["PIB", "Emprego", "Turismo", "FDI", "Receita Fiscal", "Consumo"],
    )
with col3:
    scenario = st.selectbox("Cenário", [s.capitalize() for s in SCENARIOS], index=1)

years = list(range(FORECAST_START_YEAR, FORECAST_END_YEAR + 1))

st.subheader(f"{indicator} — {country} ({scenario}) — Distribuição Probabilística")

fig = go.Figure()
fig.add_trace(go.Scatter(x=years, y=[None] * len(years), mode="lines",
                          name="P95", line=dict(width=0), showlegend=False))
fig.add_trace(go.Scatter(x=years, y=[None] * len(years), mode="lines",
                          name="P05-P95", fill="tonexty", line=dict(width=0)))
fig.add_trace(go.Scatter(x=years, y=[None] * len(years), mode="lines+markers",
                          name="Mediana (P50)"))
fig.update_layout(title=f"{indicator} — Intervalo de confiança Monte Carlo (placeholder)")
apply_theme(fig)
st.plotly_chart(fig, use_container_width=True)

data_pending_notice("Simulação Monte Carlo + ensemble (XGBoost/LightGBM/Prophet/LSTM)")

st.markdown("###")

st.subheader("Comparação de Modelos (Ensemble)")
fig2 = go.Figure()
for model_name in ["XGBoost", "LightGBM", "Prophet", "LSTM", "Ensemble"]:
    fig2.add_trace(go.Scatter(x=years, y=[None] * len(years), mode="lines", name=model_name))
fig2.update_layout(title=f"{indicator} — projeções por modelo (placeholder)")
apply_theme(fig2)
st.plotly_chart(fig2, use_container_width=True)

data_pending_notice("Treinamento e validação dos modelos (models/ml, models/montecarlo)")

st.markdown("###")

st.subheader("Riscos Extremos (Tail Risk)")
col_a, col_b = st.columns(2)
with col_a:
    st.metric("VaR 95% (downside)*", "—")
with col_b:
    st.metric("Probabilidade de cenário de estresse*", "—%")

data_pending_notice("Análise EVT (Extreme Value Theory) sobre distribuições simuladas")
