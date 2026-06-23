"""
dashboards/pages/09_forecast_center.py
Página 9 — Forecast Center
Monte Carlo 2.0 com distribuição Student-t (fat tails) via MLE.
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
from dashboards.components import page_header, apply_theme, data_pending_notice  # noqa: E402

page_header(
    "Forecast Center",
    f"Projeções {FORECAST_START_YEAR}–{FORECAST_END_YEAR} · "
    f"Monte Carlo (20.000 simulações) · Distribuição Student-t (MLE)",
)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_simulation(indicator_code: str, country_code: str):
    """Cache do Monte Carlo — evita recalcular 20k simulações a cada interação."""
    from models.montecarlo.simulation_engine import run_simulation
    return run_simulation(indicator_code, country_code)

# ------------------------------------------------------------------
# SELETORES
# ------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    country_code = st.selectbox(
        "País",
        HOST_COUNTRIES,
        format_func=lambda c: COUNTRY_NAMES[c],
    )

AVAILABLE_INDICATORS = {
    "USA": {
        "PIB Nominal": "GDP_NOMINAL",
        "PIB Real": "GDP_REAL",
        "Inflação (CPI)": "CPI",
        "Desemprego": "UNEMPLOYMENT_RATE",
    },
    "CAN": {"Turismo (Chegadas)": "TOURISM_ARRIVALS"},
    "MEX": {"Turismo (Chegadas)": "TOURISM_ARRIVALS"},
}

with col2:
    available = AVAILABLE_INDICATORS.get(country_code, {})
    if not available:
        st.selectbox("Indicador", ["— Sem dados disponíveis —"])
        indicator_code = None
        indicator_name = None
    else:
        indicator_name = st.selectbox("Indicador", list(available.keys()))
        indicator_code = available[indicator_name]

st.markdown("###")

# ------------------------------------------------------------------
# EXECUTA SIMULAÇÃO (com cache)
# ------------------------------------------------------------------
if indicator_code:
    with st.spinner(f"Calculando Monte Carlo — {indicator_name}..."):
        result = cached_simulation(indicator_code, country_code)

    if result is None:
        data_pending_notice(
            f"{indicator_name} ({COUNTRY_NAMES[country_code]}) — "
            f"dados insuficientes para simulação (mínimo 5 observações anuais)"
        )
    else:
        years = result["forecast_years"]
        p05 = [result["percentiles"][y]["p05"] for y in years]
        p25 = [result["percentiles"][y]["p25"] for y in years]
        p50 = [result["percentiles"][y]["p50"] for y in years]
        p75 = [result["percentiles"][y]["p75"] for y in years]
        p95 = [result["percentiles"][y]["p95"] for y in years]

        fig = go.Figure()

        # Banda P05-P95
        fig.add_trace(go.Scatter(
            x=years, y=p95, mode="lines",
            line=dict(width=0), showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=years, y=p05, mode="lines",
            line=dict(width=0),
            name="Banda P05–P95",
            fill="tonexty",
            fillcolor="rgba(76,139,245,0.10)",
        ))

        # Banda P25-P75
        fig.add_trace(go.Scatter(
            x=years, y=p75, mode="lines",
            line=dict(width=0), showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=years, y=p25, mode="lines",
            line=dict(width=0),
            name="Banda P25–P75",
            fill="tonexty",
            fillcolor="rgba(76,139,245,0.22)",
        ))

        # Mediana
        fig.add_trace(go.Scatter(
            x=years, y=p50, mode="lines+markers",
            line=dict(color="#4C8BF5", width=2.5),
            marker=dict(size=6, color="#4C8BF5"),
            name="Mediana (P50)",
        ))

        fig.update_layout(
            title=f"{indicator_name} — {COUNTRY_NAMES[country_code]} · "
                  f"Monte Carlo {FORECAST_START_YEAR}–{FORECAST_END_YEAR}",
        )
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        # KPIs de resumo
        p_last = result["percentiles"][years[-1]]
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("P05 (2035)", f"{p_last['p05']:,.1f}")
        col_b.metric("Mediana P50 (2035)", f"{p_last['p50']:,.1f}")
        col_c.metric("P95 (2035)", f"{p_last['p95']:,.1f}")
        col_d.metric("Média simulada (2035)", f"{p_last['mean']:,.1f}")

        st.markdown("###")

        with st.expander("📋 Tabela completa de percentis por ano"):
            rows = []
            for y in years:
                pct = result["percentiles"][y]
                rows.append({
                    "Ano": y,
                    "P05": f"{pct['p05']:,.2f}",
                    "P25": f"{pct['p25']:,.2f}",
                    "P50 Mediana": f"{pct['p50']:,.2f}",
                    "P75": f"{pct['p75']:,.2f}",
                    "P95": f"{pct['p95']:,.2f}",
                    "Média": f"{pct['mean']:,.2f}",
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        st.markdown("###")
        st.markdown("**Metodologia e limitações:**")
        
        dist_name = "Student-t (fat tails)" if result["distribution"] == "student-t" else "Normal"
        df_t = result["df_t"]
        
        st.markdown(f"""
        - **Modelo**: bootstrap paramétrico — variações anuais históricas
          modeladas como distribuição **{dist_name}**
        - **Graus de liberdade (ν)**: {df_t:.1f} — {'caudas pesadas (ν < 10)' if df_t < 10 else 'aproximação normal (ν > 20)' if df_t > 20 else 'caudas moderadas'}
        - **Última observação**: {result['last_observed_value']:,.2f} ({result['last_observed_year']})
        - **Simulações**: {result['n_simulations']:,} trajetórias · cache por 1 hora
        - **Método de variação**: {'diferença logarítmica' if indicator_code in {'GDP_NOMINAL', 'GDP_REAL', 'CPI', 'TOURISM_ARRIVALS'} else 'variação percentual'}
        - **Limitações**: assume IID (ignora autocorrelação e GARCH),
          não modela regime switching, ignora correlação entre indicadores,
          não modela choques exógenos (Copa 2026, geopolítica).
        """)
else:
    data_pending_notice(
        f"Dados macro de {COUNTRY_NAMES[country_code]} ainda não integrados. "
        f"Selecione Estados Unidos para simulação completa."
    )

st.markdown("###")
data_pending_notice(
    "Ensemble ML (XGBoost/LightGBM/Prophet/LSTM) — fase pós-MVP."
)
