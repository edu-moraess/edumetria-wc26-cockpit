"""
dashboards/pages/01_executive_overview.py
Página 1 — Executive Overview
KPIs institucionais (baseline FIFA, pendente de auditoria) +
snapshot de mercado em tempo real (dados via yfinance).
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import FIFA_BASELINE, HOST_COUNTRIES, COUNTRY_NAMES, WCLI_CLASSIFICATION  # noqa: E402
from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header(
    "Executive Overview",
    "Síntese executiva do impacto econômico líquido — FIFA World Cup 2026™ "
    "(EUA · Canadá · México)",
)


@st.cache_data(ttl=600)
def load_indicator(indicator_code: str) -> pd.DataFrame:
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value
            FROM fact_indicator_values
            WHERE indicator_code = ?
            ORDER BY period
            """,
            [indicator_code],
        ).df()
    df["period"] = pd.to_datetime(df["period"])
    return df


scope = st.selectbox(
    "Escopo geográfico",
    ["Consolidado (3 países)"] + [COUNTRY_NAMES[c] for c in HOST_COUNTRIES],
)

st.caption(
    "Valores baseline a partir do FIFA 2026 Socioeconomic Impact Analysis "
    "(sujeitos a auditoria — ver seção de Auditoria Crítica no white paper). "
    "KPIs marcados com * são placeholders até integração da modelagem econômica."
)

# ------------------------------------------------------------------
# KPI GRID — LINHA 1 (modelagem econômica, ainda pendente)
# ------------------------------------------------------------------
kpi_row([
    ("PIB Incremental (líquido)*", "US$ — bn", None),
    ("Receita Fiscal*", "US$ — bn", None),
    ("Empregos (FTE)*", "—", None),
    ("Turismo (visitantes incrementais)*", "—", None),
])

# ------------------------------------------------------------------
# KPI GRID — LINHA 2 (modelagem econômica, ainda pendente)
# ------------------------------------------------------------------
kpi_row([
    ("FDI Atraído (cumulativo 2026-2035)*", "US$ — bn", None),
    ("World Cup Legacy Index (WCLI)*", "—", None),
    ("Fluxo Aéreo (variação)*", "—%", None),
    ("Ocupação Hoteleira (pico)*", "—%", None),
])

st.markdown("###")

# ------------------------------------------------------------------
# SNAPSHOT DE MERCADO — DADOS REAIS (yfinance)
# ------------------------------------------------------------------
st.subheader("📡 Snapshot de Mercado (dados reais — atualizado via pipeline ETL)")

market_kpis = []
for code, label, fmt in [
    ("SP500", "S&P 500", "{:,.0f}"),
    ("TSX", "TSX Composite", "{:,.0f}"),
    ("IPC_MEXICO", "IPC México", "{:,.0f}"),
    ("VIX", "VIX", "{:,.2f}"),
]:
    df = load_indicator(code)
    if not df.empty:
        last = df["value"].iloc[-1]
        prev = df["value"].iloc[-2] if len(df) > 1 else last
        delta_pct = (last / prev - 1) * 100 if prev else 0
        market_kpis.append((label, fmt.format(last), f"{delta_pct:+.2f}%"))
    else:
        market_kpis.append((label, "—", None))

kpi_row(market_kpis)

st.markdown("###")

# ------------------------------------------------------------------
# REFERÊNCIA — BASELINE FIFA (BRUTO, NÃO AUDITADO)
# ------------------------------------------------------------------
with st.expander("📋 Referência: Indicadores Brutos FIFA (ponto de partida, pré-auditoria)"):
    g = FIFA_BASELINE["global"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Output Global", f"US$ {g['output_usd_bn']} bn")
        st.metric("PIB Global Adicional", f"US$ {g['gdp_usd_bn']} bn")
    with col2:
        st.metric("Empregos FTE", f"{g['jobs_fte']:,}")
        st.metric("Visitantes Totais", f"{g['visitors_total']:,}")
    with col3:
        st.metric("SROI", f"{g['sroi']}")
        st.metric("Benefícios Sociais", f"US$ {g['social_benefits_usd_bn']} bn")

    st.markdown("**Por país-sede (bruto FIFA):**")
    usa, can, mex = FIFA_BASELINE["USA"], FIFA_BASELINE["CAN"], FIFA_BASELINE["MEX"]
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("**🇺🇸 Estados Unidos**")
        st.write(f"Gasto total: US$ {usa['spend_usd_bn']} bn")
        st.write(f"Output: US$ {usa['output_usd_bn']} bn")
        st.write(f"PIB: US$ {usa['gdp_usd_bn']} bn")
        st.write(f"Empregos: {usa['jobs']:,}")
        st.write(f"Receita governamental: US$ {usa['gov_revenue_usd_bn']} bn")
    with t2:
        st.markdown("**🇨🇦 Canadá**")
        st.write(f"Output: CAD {can['output_cad_bn']} bn")
        st.write(f"PIB: CAD {can['gdp_cad_bn']} bn")
        st.write(f"Empregos: {can['jobs']:,}")
    with t3:
        st.markdown("**🇲🇽 México**")
        st.write(f"Impacto (baixo): US$ {mex['impact_usd_bn_low']} bn")
        st.write(f"Impacto (alto, metodologia alt.): MX$ {mex['impact_mxn_bn_high']} bn")

st.markdown("###")

# ------------------------------------------------------------------
# GRÁFICO — TURISMO REAL (CAN + MEX) — ÚLTIMOS DADOS DISPONÍVEIS
# ------------------------------------------------------------------
st.subheader("Turismo Internacional — Séries Reais (Canadá e México)")

fig = go.Figure()
has_data = False
for country_code, label, color in [("CAN", "Canadá (StatCan)", "#3FB68B"), ("MEX", "México (Banxico)", "#C9A227")]:
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
    if not df.empty:
        df["period"] = pd.to_datetime(df["period"])
        fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines+markers", name=label, line=dict(color=color)))
        has_data = True

fig.update_layout(title="Chegadas de turistas internacionais — série histórica")
apply_theme(fig)

if has_data:
    st.plotly_chart(fig, use_container_width=True)
else:
    data_pending_notice("Turismo — sem dados carregados (rode o pipeline ETL)")

st.markdown("###")

# ------------------------------------------------------------------
# WCLI — TABELA DE CLASSIFICAÇÃO DE REFERÊNCIA
# ------------------------------------------------------------------
st.subheader("World Cup Legacy Index (WCLI) — Escala de Classificação")

wcli_df = pd.DataFrame(WCLI_CLASSIFICATION, columns=["De", "Até", "Classificação"])
st.dataframe(wcli_df, hide_index=True, use_container_width=True)

data_pending_notice("Cálculo do WCLI por país e cenário — depende de impacto líquido/contrafactual")