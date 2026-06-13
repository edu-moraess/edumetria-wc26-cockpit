"""
dashboards/pages/01_executive_overview.py
Página 1 — Executive Overview
KPIs: PIB Incremental, Receita Fiscal, Empregos, Turismo, FDI, WCLI,
Fluxo Aéreo, Ocupação Hoteleira.
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import FIFA_BASELINE, HOST_COUNTRIES, COUNTRY_NAMES, WCLI_CLASSIFICATION  # noqa: E402
from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402

page_header(
    "Executive Overview",
    "Síntese executiva do impacto econômico líquido — FIFA World Cup 2026™ "
    "(EUA · Canadá · México)",
)

scope = st.selectbox(
    "Escopo geográfico",
    ["Consolidado (3 países)"] + [COUNTRY_NAMES[c] for c in HOST_COUNTRIES],
)

st.caption(
    "Valores baseline a partir do FIFA 2026 Socioeconomic Impact Analysis "
    "(sujeitos a auditoria — ver seção de Auditoria Crítica no white paper). "
    "KPIs marcados com * são placeholders até integração do pipeline ETL."
)

kpi_row([
    ("PIB Incremental (líquido)*", "US$ — bn", None),
    ("Receita Fiscal*", "US$ — bn", None),
    ("Empregos (FTE)*", "—", None),
    ("Turismo (visitantes incrementais)*", "—", None),
])

kpi_row([
    ("FDI Atraído (cumulativo 2026-2035)*", "US$ — bn", None),
    ("World Cup Legacy Index (WCLI)*", "—", None),
    ("Fluxo Aéreo (variação)*", "—%", None),
    ("Ocupação Hoteleira (pico)*", "—%", None),
])

st.markdown("###")

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

st.subheader("Impacto Bruto vs. Líquido vs. Contrafactual")

fig = go.Figure()
fig.add_trace(go.Bar(name="Bruto (FIFA)", x=["EUA", "Canadá", "México"], y=[30.5, 2.0, 3.0]))
fig.add_trace(go.Bar(name="Líquido (estimado)*", x=["EUA", "Canadá", "México"], y=[None, None, None]))
fig.add_trace(go.Bar(name="Contrafactual (sem evento)*", x=["EUA", "Canadá", "México"], y=[None, None, None]))
fig.update_layout(barmode="group", title="PIB Adicional — US$ bn (placeholder)")
apply_theme(fig)
st.plotly_chart(fig, use_container_width=True)

data_pending_notice("Modelagem de impacto líquido/contrafactual")

st.markdown("###")

st.subheader("World Cup Legacy Index (WCLI) — Escala de Classificação")
import pandas as pd  # noqa: E402

wcli_df = pd.DataFrame(WCLI_CLASSIFICATION, columns=["De", "Até", "Classificação"])
st.dataframe(wcli_df, hide_index=True, use_container_width=True)

data_pending_notice("Cálculo do WCLI por país e cenário")
