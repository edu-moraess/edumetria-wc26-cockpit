"""
dashboards/pages/07_geopolitica.py
Página 7 — Geopolítica e Risco Global
VERSÃO v4: Sem HTML mal formatado, dados em tempo real, componentes nativos Streamlit
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import THEME, HOST_COUNTRIES, COUNTRY_NAMES, REALTIME_REFRESH_SECONDS  # noqa: E402
from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header(
    "Geopolítica e Risco Global",
    "Avaliação de risco sistêmico, geopolítico e energético",
)

@st.cache_data(ttl=REALTIME_REFRESH_SECONDS)
def load_indicator(indicator_code: str, country_code: str = None) -> pd.DataFrame:
    with get_connection() as conn:
        if country_code:
            df = conn.execute(
                "SELECT period, value FROM fact_indicator_values WHERE indicator_code = ? AND country_code = ? ORDER BY period",
                [indicator_code, country_code],
            ).df()
        else:
            df = conn.execute(
                "SELECT period, value FROM fact_indicator_values WHERE indicator_code = ? ORDER BY period",
                [indicator_code],
            ).df()
        df["period"] = pd.to_datetime(df["period"])
        return df


# ------------------------------------------------------------------
# KPIs — DADOS REAIS
# ------------------------------------------------------------------
st.subheader("Métricas de Risco (dados reais)")

risk_kpis = []
for code, label, fmt in [
    ("VIX", "VIX", "{:.2f}"),
    ("WTI_CRUDE", "WTI Crude", "${:.2f}"),
    ("BRENT_CRUDE", "Brent Crude", "${:.2f}"),
    ("NATURAL_GAS", "Gás Natural", "${:.2f}"),
    ("GOLD", "Ouro", "${:.2f}"),
]:
    df = load_indicator(code)
    if not df.empty:
        last = df["value"].iloc[-1]
        prev = df["value"].iloc[-2] if len(df) > 1 else last
        delta = ((last / prev - 1) * 100) if prev else 0
        risk_kpis.append((label, fmt.format(last), f"{delta:+.2f}%"))
    else:
        risk_kpis.append((label, "—", None))

kpi_row(risk_kpis)

st.markdown("###")

# ------------------------------------------------------------------
# GRÁFICO — VIX
# ------------------------------------------------------------------
st.subheader("VIX — Volatilidade Implícita (S&P 500)")

vix_df = load_indicator("VIX")
if not vix_df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=vix_df["period"], y=vix_df["value"],
        mode="lines", name="VIX", line=dict(color="#FF4560", width=1.5)
    ))
    fig.add_hline(y=20, line_dash="dash", line_color="#FFB300", annotation_text="Normal (20)")
    fig.add_hline(y=30, line_dash="dash", line_color="#FF4560", annotation_text="Alerta (30)")
    fig.add_hline(y=40, line_dash="dash", line_color="#FF0000", annotation_text="Crise (40)")
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    data_pending_notice("VIX — sem dados carregados")

st.markdown("###")

# ------------------------------------------------------------------
# GRÁFICO — Commodities
# ------------------------------------------------------------------
st.subheader("Commodities — Energia e Ouro")

fig = go.Figure()
has_data = False
for code, label, color in [
    ("WTI_CRUDE", "WTI Crude", "#4C8BF5"),
    ("BRENT_CRUDE", "Brent Crude", "#00C8FF"),
    ("NATURAL_GAS", "Gás Natural", "#A78BFA"),
    ("GOLD", "Ouro", "#FFB300"),
]:
    df = load_indicator(code)
    if not df.empty:
        fig.add_trace(go.Scatter(
            x=df["period"], y=df["value"],
            mode="lines", name=label, line=dict(color=color, width=1.5)
        ))
        has_data = True

if has_data:
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    data_pending_notice("Commodities — sem dados carregados")

st.markdown("###")

# ------------------------------------------------------------------
# RISK SCORE
# ------------------------------------------------------------------
st.subheader("World Cup Risk Score 2.0")

from models.montecarlo.risk_score_v2 import RiskScoreV2  # noqa: E402

try:
    risk_engine = RiskScoreV2()
    risk_score = risk_engine.calculate()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score Total", f"{risk_score.total:.1f}")
    col2.metric("Financeiro (35%)", f"{risk_score.financial:.1f}")
    col3.metric("Energético (25%)", f"{risk_score.energy:.1f}")
    col4.metric("Macro (25%)", f"{risk_score.macro:.1f}")
    
    st.caption("Geopolítico (15%) — GPR Index pendente")
    
except Exception as e:
    st.error(f"Erro ao calcular Risk Score: {e}")

st.markdown("###")

# ------------------------------------------------------------------
# Análise Geopolítica
# ------------------------------------------------------------------
st.subheader("Análise Geopolítica — Contexto Copa 2026")

with st.expander("🇺🇸 Estados Unidos — Risco Geopolítico", expanded=True):
    st.markdown("""
    - **Ameaça terrorista**: Baixa-moderada (infraestrutura de segurança robusta)
    - **Tensão com México**: Moderada (imigração, comércio)
    - **Relações com Canadá**: Baixa (aliado histórico)
    - **Risco cibernético**: Alto (evento global, alvo atraente)
    """)

with st.expander("🇨🇦 Canadá — Risco Geopolítico"):
    st.markdown("""
    - **Ameaça terrorista**: Baixa
    - **Tensão com EUA**: Baixa-moderada (tarifas, comércio)
    - **Risco cibernético**: Moderado
    """)

with st.expander("🇲🇽 México — Risco Geopolítico"):
    st.markdown("""
    - **Ameaça terrorista**: Moderada (cartéis, violência organizada)
    - **Tensão com EUA**: Moderada-alta (imigração, narcotráfico, USMCA)
    - **Risco cibernético**: Moderado
    """)
