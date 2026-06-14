"""
dashboards/pages/09_forecast_center.py
Página 9 — Forecast Center
Monte Carlo real com dados históricos do banco.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import (  # noqa: E402
    HOST_COUNTRIES, COUNTRY_NAMES,
    FORECAST_START_YEAR, FORECAST_END_YEAR,
)
from dashboards.components import page_header, apply_theme, data_pending_notice  # noqa: E402
from models.montecarlo.simulation_engine import run_simulation  # noqa: E402

page_header(
    "Forecast Center",
    f"Projeções {FORECAST_START_YEAR}–{FORECAST_END_YEAR} · "
    f"Monte Carlo (20.000 simulações) · Bootstrap paramétrico",
)

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
    "CAN": {
        "Turismo (Chegadas)": "TOURISM_ARRIVALS",
    },
    "MEX": {
        "Turismo (Chegadas)": "TOURISM_ARRIVALS",
    },
}

with col2:
    available = AVAILABLE_INDICATORS.get(country_code, {})
    if not available:
        indicator_name = None
        indicator_code = None
        st.selectbox("Indicador", ["— Sem dados disponíveis —"])
    else:
        indicator_name = st.selectbox("Indicador", list(available.keys()))
        indicator_code = available[indicator_name]

st.markdown("###")

# ------------------------------------------------------------------
# EXECUTA SIMULAÇÃO
# ------------------------------------------------------------------
if indicator_code:
    with st.spinner(f"Rodando Monte Carlo ({indicator_name} — {COUNTRY_NAMES[country_code]})..."):
        result = run_simulation(indicator_code, country_code)

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

        # ------------------------------------------------------------------
        # GRÁFICO PRINCIPAL — bandas de confiança
        # ------------------------------------------------------------------
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=years, y=p95, mode="lines", line=dict(width=0),
            name="P95", showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=years, y=p05, mode="lines", line=dict(width=0),
            name="Banda P05-P95", fill="tonexty",
            fillcolor="rgba(201,162,39,0.15)",
        ))
        fig.add_trace(go.Scatter(
            x=years, y=p75, mode="lines", line=dict(width=0),
            name="P75", showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=years, y=p25, mode="lines", line=dict(width=0),
            name="Banda P25-P75", fill="tonexty",
            fillcolor="rgba(201,162,39,0.25)",
        ))
        fig.add_trace(go.Scatter(
            x=years, y=p50, mode="lines+markers",
            line=dict(color="#C9A227", width=2.5),
            marker=dict(size=7),
            name="Mediana (P50)",
        ))

        fig.update_layout(
            title=f"{indicator_name} — {COUNTRY_NAMES[country_code]} · "
                  f"Monte Carlo {FORECAST_START_YEAR}–{FORECAST_END_YEAR}",
        )
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        # ------------------------------------------------------------------
        # KPIs de resumo
        # ------------------------------------------------------------------
        last_year = years[-1]
        p = result["percentiles"][last_year]

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("P05 (2035)", f"{p['p05']:,.1f}")
        col_b.metric("P50 — Mediana (2035)", f"{p['p50']:,.1f}")
        col_c.metric("P95 (2035)", f"{p['p95']:,.1f}")
        col_d.metric("Média simulada (2035)", f"{p['mean']:,.1f}")

        st.markdown("###")

        # ------------------------------------------------------------------
        # TABELA COMPLETA DE PERCENTIS
        # ------------------------------------------------------------------
        with st.expander("📋 Tabela completa de percentis por ano"):
            rows = []
            for y in years:
                pct = result["percentiles"][y]
                rows.append({
                    "Ano": y,
                    "P05": f"{pct['p05']:,.2f}",
                    "P25": f"{pct['p25']:,.2f}",
                    "P50 (Mediana)": f"{pct['p50']:,.2f}",
                    "P75": f"{pct['p75']:,.2f}",
                    "P95": f"{pct['p95']:,.2f}",
                    "Média": f"{pct['mean']:,.2f}",
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        # ------------------------------------------------------------------
        # METODOLOGIA
        # ------------------------------------------------------------------
        st.markdown("###")
        st.markdown("**Metodologia e limitações:**")
        st.markdown(
            f"""
            - **Modelo**: bootstrap paramétrico — variações anuais históricas
              modeladas como distribuição normal (μ = {result['mu']*100:.2f}%,
              σ = {result['sigma']*100:.2f}% a.a.)
            - **Última observação**: {result['last_observed_value']:,.2f}
              ({result['last_observed_year']})
            - **Simulações**: 20.000 trajetórias independentes
            - **Limitações**: assume normalidade dos incrementos (ignora fat
              tails), ignora correlação entre indicadores e países, não modela
              choques exógenos (Copa 2026, tensões geopolíticas). Fase
              pós-MVP: EVT para caudas e modelos estruturais com shocks.
            """
        )
else:
    data_pending_notice(
        f"Dados macro de {COUNTRY_NAMES[country_code]} ainda não integrados "
        f"(extractors StatCan macro e INEGI pendentes de token de acesso). "
        f"Selecione Estados Unidos para simulação completa."
    )

st.markdown("###")

data_pending_notice(
    "Ensemble ML (XGBoost/LightGBM/Prophet/LSTM) — fase pós-MVP. "
    "Monte Carlo paramétrico disponível acima para indicadores com dados reais."
)