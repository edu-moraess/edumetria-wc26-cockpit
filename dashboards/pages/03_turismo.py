"""
dashboards/pages/03_turismo.py
Página 3 — Turismo Internacional
Dados reais: Canadá (StatCan) e México (Banxico).
EUA (NTTO) pendente de integração manual.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import FIFA_BASELINE, HOST_COUNTRIES, COUNTRY_NAMES  # noqa: E402
from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Turismo Internacional", "Visitantes · Gastos · Permanência · Fluxos")


@st.cache_data(ttl=600)
def load_tourism(country_code: str) -> pd.DataFrame:
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value
            FROM fact_indicator_values
            WHERE country_code = ? AND indicator_code = 'TOURISM_ARRIVALS'
            ORDER BY period
            """,
            [country_code],
        ).df()
    df["period"] = pd.to_datetime(df["period"])
    return df


# ------------------------------------------------------------------
# KPIs
# ------------------------------------------------------------------
kpi_items = [("Visitantes Totais (baseline FIFA 2026)", f"{FIFA_BASELINE['global']['visitors_total']:,}", None)]

for code, label in [("CAN", "Canadá — último valor"), ("MEX", "México — último valor")]:
    df = load_tourism(code)
    if not df.empty:
        last = df.iloc[-1]
        kpi_items.append((label, f"{last['value']:,.0f}", f"{last['period'].strftime('%b/%Y')}"))
    else:
        kpi_items.append((label, "—", None))

kpi_row(kpi_items[:4])

st.markdown("###")

# ------------------------------------------------------------------
# SÉRIES HISTÓRICAS — CANADÁ E MÉXICO
# ------------------------------------------------------------------
country_code = st.selectbox(
    "País",
    ["CAN", "MEX", "USA"],
    format_func=lambda c: COUNTRY_NAMES[c],
)

tabs = st.tabs(["Série Histórica", "Setores Beneficiados (estimativa)", "Comparação CAN vs MEX"])

with tabs[0]:
    st.subheader(f"Chegadas de turistas internacionais — {COUNTRY_NAMES[country_code]}")

    if country_code == "USA":
        st.warning(
            "⚠️ Dados de turismo dos EUA (US NTTO) não têm API automática. "
            "Para integrar: baixar relatórios em "
            "https://www.trade.gov/national-travel-tourism-office e colocar "
            "em `data/external/ntto_usa/`."
        )
        data_pending_notice("Turismo EUA (NTTO) — download manual pendente")
    else:
        source_name = "StatCan" if country_code == "CAN" else "Banxico"
        df = load_tourism(country_code)

        if df.empty:
            data_pending_notice(f"Turismo {COUNTRY_NAMES[country_code]} — sem dados carregados")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["period"], y=df["value"], mode="lines+markers",
                name="Chegadas de turistas", line=dict(color="#C9A227"),
            ))
            fig.update_layout(title=f"Chegadas de turistas internacionais — fonte: {source_name}")
            apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

            st.caption(
                f"Série: {len(df)} observações · "
                f"Período: {df['period'].min().strftime('%b/%Y')} a {df['period'].max().strftime('%b/%Y')} · "
                f"Fonte: {source_name}"
            )

with tabs[1]:
    st.subheader("Impacto setorial estimado")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Hotelaria", "Aviação", "Restaurantes", "Varejo", "Entretenimento"],
        y=[None, None, None, None, None],
        name="Receita incremental (US$ bn)",
    ))
    fig.update_layout(title="Receita incremental por setor (placeholder)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    data_pending_notice("Decomposição setorial — requer modelo de gasto médio por visitante (Input-Output)")

with tabs[2]:
    st.subheader("Comparação: Canadá vs. México")
    fig = go.Figure()
    has_data = False
    for code, label, color in [("CAN", "Canadá (StatCan)", "#3FB68B"), ("MEX", "México (Banxico)", "#C9A227")]:
        df = load_tourism(code)
        if not df.empty:
            fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=label, line=dict(color=color)))
            has_data = True
    fig.update_layout(title="Chegadas de turistas internacionais — comparação")
    apply_theme(fig)
    if has_data:
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Comparação CAN vs MEX — sem dados carregados")