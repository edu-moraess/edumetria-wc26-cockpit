"""
dashboards/pages/09_forecast_center.py
Página 9 — Forecast Center
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import HOST_COUNTRIES, COUNTRY_NAMES, FORECAST_START_YEAR, FORECAST_END_YEAR  # noqa: E402
from dashboards.components import page_header, apply_theme  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Forecast Center", f"Projeções {FORECAST_START_YEAR}–{FORECAST_END_YEAR} · Monte Carlo")

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

@st.cache_data(ttl=3600, show_spinner=False)
def cached_simulation(indicator_code: str, country_code: str):
    from models.montecarlo.simulation_engine import run_simulation
    return run_simulation(indicator_code, country_code)

col1, col2 = st.columns(2)
with col1:
    country_code = st.selectbox("País", HOST_COUNTRIES, format_func=lambda c: COUNTRY_NAMES[c])

AVAILABLE_INDICATORS = {
    "USA": {"PIB Nominal": "GDP_NOMINAL", "PIB Real": "GDP_REAL", "Inflação (CPI)": "CPI", "Desemprego": "UNEMPLOYMENT_RATE"},
    "CAN": {"Turismo (Chegadas)": "TOURISM_ARRIVALS"},
    "MEX": {"Turismo (Chegadas)": "TOURISM_ARRIVALS"},
}

with col2:
    available = AVAILABLE_INDICATORS.get(country_code, {})
    if not available:
        st.selectbox("Indicador", ["— Sem dados disponíveis —"])
        indicator_code = None
    else:
        indicator_name = st.selectbox("Indicador", list(available.keys()))
        indicator_code = available[indicator_name]

st.markdown("###")

if indicator_code:
    with st.spinner(f"Calculando Monte Carlo — {indicator_name}..."):
        result = cached_simulation(indicator_code, country_code)

    if result is None:
        st.info(f"⏳ Dados insuficientes para simulação de {indicator_name} ({COUNTRY_NAMES[country_code]})")
    else:
        years = result["forecast_years"]
        p05 = [result["percentiles"][y]["p05"] for y in years]
        p25 = [result["percentiles"][y]["p25"] for y in years]
        p50 = [result["percentiles"][y]["p50"] for y in years]
        p75 = [result["percentiles"][y]["p75"] for y in years]
        p95 = [result["percentiles"][y]["p95"] for y in years]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=years, y=p95, mode="lines", line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=years, y=p05, mode="lines", line=dict(width=0), name="Banda P05–P95", fill="tonexty", fillcolor="rgba(76,139,245,0.10)"))
        fig.add_trace(go.Scatter(x=years, y=p75, mode="lines", line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=years, y=p25, mode="lines", line=dict(width=0), name="Banda P25–P75", fill="tonexty", fillcolor="rgba(76,139,245,0.22)"))
        fig.add_trace(go.Scatter(x=years, y=p50, mode="lines+markers", line=dict(color="#4C8BF5", width=2.5), marker=dict(size=6), name="Mediana (P50)"))

        fig.update_layout(title=f"{indicator_name} — {COUNTRY_NAMES[country_code]} · Monte Carlo {FORECAST_START_YEAR}–{FORECAST_END_YEAR}")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        p_last = result["percentiles"][years[-1]]
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("P05 (2035)", f"{p_last['p05']:,.1f}")
        col_b.metric("Mediana P50 (2035)", f"{p_last['p50']:,.1f}")
        col_c.metric("P95 (2035)", f"{p_last['p95']:,.1f}")
        col_d.metric("Média (2035)", f"{p_last['mean']:,.1f}")

        with st.expander("📋 Tabela completa de percentis"):
            rows = []
            for y in years:
                pct = result["percentiles"][y]
                rows.append({"Ano": y, "P05": f"{pct['p05']:,.2f}", "P25": f"{pct['p25']:,.2f}", "P50": f"{pct['p50']:,.2f}", "P75": f"{pct['p75']:,.2f}", "P95": f"{pct['p95']:,.2f}", "Média": f"{pct['mean']:,.2f}"})
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        dist_name = "Student-t (fat tails)" if result["distribution"] == "student-t" else "Normal"
        st.markdown(f"""
        **Metodologia:**
        - Distribuição: **{dist_name}** (ν={result['df_t']:.1f})
        - Última observação: {result['last_observed_value']:,.2f} ({result['last_observed_year']})
        - Simulações: {result['n_simulations']:,}
        """)
else:
    st.info("⏳ Selecione um indicador para simular")

st.markdown("###")
st.info("⏳ Ensemble ML (XGBoost/Prophet/LSTM) — fase pós-MVP")
