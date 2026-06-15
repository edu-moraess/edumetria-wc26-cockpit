"""
dashboards/pages/03_turismo.py
Página 3 — Turismo Internacional
Ajustado para exibir dados apenas quando selecionar EUA.
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import FIFA_BASELINE, COUNTRY_NAMES  # noqa: E402
from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Turismo Internacional", "Visitantes · Gastos · Permanência · Fluxos")

# ------------------------------------------------------------------
# KPIs — baseline global
# ------------------------------------------------------------------
kpi_items = [("Visitantes Totais (baseline FIFA 2026)", f"{FIFA_BASELINE['global']['visitors_total']:,}", None)]
kpi_row(kpi_items)

st.markdown("###")

# ------------------------------------------------------------------
# Seleção de país
# ------------------------------------------------------------------
country_code = st.selectbox("País", ["USA"], format_func=lambda c: COUNTRY_NAMES.get(c, c))

tabs = st.tabs(["Série Histórica", "Setores Beneficiados (em desenvolvimento)", "Comparação CAN vs MEX"])

# ------------------------------------------------------------------
# Aba 1 — Série Histórica
# ------------------------------------------------------------------
with tabs[0]:
    st.subheader(f"Chegadas de turistas internacionais — {COUNTRY_NAMES[country_code]}")

    if country_code == "USA":
        try:
            with get_connection() as conn:
                df = conn.execute("""
                    SELECT country_code, indicator_code, value, ingested_at
                    FROM fact_indicator_values
                    WHERE country_code = 'USA'
                    ORDER BY ingested_at DESC
                    LIMIT 20
                """).fetchdf()

            if df.empty:
                data_pending_notice("Turismo EUA — sem dados carregados")
            else:
                st.metric("Total de Registros EUA", f"{len(df):,}")
                st.dataframe(df)

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["ingested_at"], y=df["value"], mode="lines+markers",
                    name="Indicador EUA", line=dict(color="#C9A227"),
                ))
                fig.update_layout(title="Indicadores recentes — EUA")
                apply_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")

# ------------------------------------------------------------------
# Aba 2 — Setores Beneficiados
# ------------------------------------------------------------------
with tabs[1]:
    st.subheader("Decomposição setorial do gasto turístico")
    data_pending_notice("Modelo Input-Output (multiplicadores setoriais)")

# ------------------------------------------------------------------
# Aba 3 — Comparação CAN vs MEX
# ------------------------------------------------------------------
with tabs[2]:
    st.subheader("Comparação: Canadá vs. México")
    data_pending_notice("Comparação CAN vs MEX — sem dados carregados")