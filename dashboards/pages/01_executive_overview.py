"""
dashboards/pages/01_executive_overview.py
Página 1 — Executive Overview
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
from dashboards.components import page_header, kpi_row, apply_theme  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Executive Overview", "Síntese executiva — FIFA World Cup 2026™")


def load_indicator(indicator_code: str, country_code: str = None) -> pd.DataFrame:
    try:
        with get_connection() as conn:
            if country_code:
                df = conn.execute("SELECT period, value FROM fact_indicator_values WHERE indicator_code = ? AND country_code = ? ORDER BY period", [indicator_code, country_code]).df()
            else:
                df = conn.execute("SELECT period, value FROM fact_indicator_values WHERE indicator_code = ? ORDER BY period", [indicator_code]).df()
        df["period"] = pd.to_datetime(df["period"])
        return df
    except Exception:
        return pd.DataFrame(columns=["period", "value"])


# Verifica se há dados
has_data = False
try:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
        has_data = count > 0
except:
    pass

if not has_data:
    st.warning("⚠️ **Sem dados disponíveis**")
    st.info("""
    Para visualizar esta página:
    1. **No Streamlit Cloud**: Clique em **"🎲 Criar dados de demonstração"** na sidebar
    2. **Localmente**: Rode `python -m etl.run_pipeline` para dados reais
    """)
    st.stop()

# ============ CONTEÚDO COM DADOS ============

scope = st.selectbox("Escopo geográfico", ["Consolidado (3 países)"] + [COUNTRY_NAMES[c] for c in HOST_COUNTRIES])

# KPIs
sp500_df = load_indicator("SP500")
vix_df = load_indicator("VIX")

sp500_last = sp500_df["value"].iloc[-1] if not sp500_df.empty else None
sp500_delta = ((sp500_df["value"].iloc[-1] / sp500_df["value"].iloc[-2] - 1) * 100) if len(sp500_df) > 1 else None
vix_last = vix_df["value"].iloc[-1] if not vix_df.empty else None

from models.montecarlo.wcli_calculator import calculate_wcli  # noqa: E402
wcli_scores = {cc: calculate_wcli(cc) for cc in HOST_COUNTRIES}
avg_wcli = sum(r["wcli_total"] for r in wcli_scores.values() if r["wcli_total"] is not None) / sum(1 for r in wcli_scores.values() if r["wcli_total"] is not None) if any(r["wcli_total"] for r in wcli_scores.values()) else None

kpi_row([
    ("S&P 500", f"{sp500_last:,.0f}" if sp500_last else "—", f"{sp500_delta:+.2f}%" if sp500_delta else None),
    ("VIX", f"{vix_last:.2f}" if vix_last else "—", None),
    ("WCLI Médio", f"{avg_wcli:.1f}" if avg_wcli else "—", None),
    ("Visitantes FIFA (est.)", f"{FIFA_BASELINE['global']['visitors_total']:,}", None),
])

# KPIs linha 2
fdi_scores = {cc: wcli_scores[cc]["scores"].get("fdi") for cc in HOST_COUNTRIES}
avg_fdi = sum(f for f in fdi_scores.values() if f is not None) / sum(1 for f in fdi_scores.values() if f is not None) if any(fdi_scores.values()) else None

kpi_row([
    ("PIB Incremental (líquido)*", f"US$ {FIFA_BASELINE['global']['gdp_usd_bn']} bn", None),
    ("Receita Fiscal*", f"US$ {FIFA_BASELINE['USA']['gov_revenue_usd_bn']} bn", None),
    ("Empregos (FTE)", f"{FIFA_BASELINE['global']['jobs_fte']:,}", None),
    ("FDI Score", f"{avg_fdi:.1f}" if avg_fdi else "—", None),
])

st.markdown("###")

# Snapshot de mercado
st.subheader("📡 Snapshot de Mercado (dados reais — atualizado via pipeline ETL)")
market_kpis = []
for code, label, fmt in [("SP500", "S&P 500", "{:,.0f}"), ("TSX", "TSX Composite", "{:,.0f}"), ("IPC_MEXICO", "IPC México", "{:,.0f}"), ("VIX", "VIX", "{:,.2f}")]:
    df = load_indicator(code)
    if not df.empty:
        last, prev = df["value"].iloc[-1], df["value"].iloc[-2] if len(df) > 1 else df["value"].iloc[-1]
        delta_pct = (last / prev - 1) * 100 if prev else 0
        market_kpis.append((label, fmt.format(last), f"{delta_pct:+.2f}%"))
    else:
        market_kpis.append((label, "—", None))
kpi_row(market_kpis)

st.markdown("###")

# Referência FIFA
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

# Turismo
st.subheader("Turismo Internacional — Séries Reais (Canadá e México)")
fig = go.Figure()
has_tourism = False
for country_code, label, color in [("CAN", "Canadá (StatCan)", "#3FB68B"), ("MEX", "México (Banxico)", "#C9A227")]:
    with get_connection() as conn:
        df = conn.execute("SELECT period, value FROM fact_indicator_values WHERE country_code = ? AND indicator_code = 'TOURISM_ARRIVALS' ORDER BY period", [country_code]).df()
        if not df.empty:
            df["period"] = pd.to_datetime(df["period"])
            fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines+markers", name=label, line=dict(color=color)))
            has_tourism = True

if has_tourism:
    fig.update_layout(title="Chegadas de turistas internacionais — série histórica")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⏳ Dados de turismo não carregados (rode o pipeline ETL)")

st.markdown("###")

# WCLI
st.subheader("World Cup Legacy Index (WCLI) — Cálculo Completo")
wcli_rows = []
for cc in HOST_COUNTRIES:
    result = calculate_wcli(cc)
    wcli_rows.append({
        "País": COUNTRY_NAMES[cc],
        "WCLI": f"{result['wcli_total']:.1f}" if result["wcli_total"] is not None else "—",
        "Classificação": result["classification"],
        "Completeness": f"{result['completeness_pct']:.0f}%",
        "Turismo": f"{result['scores']['turismo']:.1f}" if result['scores']['turismo'] else "—",
        "PIB": f"{result['scores']['pib']:.1f}" if result['scores']['pib'] else "—",
        "Emprego": f"{result['scores']['emprego']:.1f}" if result['scores']['emprego'] else "—",
        "FDI": f"{result['scores']['fdi']:.1f}" if result['scores']['fdi'] else "—",
        "Infra": f"{result['scores']['infraestrutura']:.1f}" if result['scores']['infraestrutura'] else "—",
        "ESG": f"{result['scores']['esg']:.1f}" if result['scores']['esg'] else "—",
    })
st.dataframe(pd.DataFrame(wcli_rows), hide_index=True, use_container_width=True)

st.caption("WCLI v4: Completeness indica fração do índice com dados reais")

st.markdown("###")

st.subheader("Escala de Classificação WCLI")
wcli_scale_df = pd.DataFrame(WCLI_CLASSIFICATION, columns=["De", "Até", "Classificação"])
st.dataframe(wcli_scale_df, hide_index=True, use_container_width=True)
