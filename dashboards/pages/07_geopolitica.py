"""
dashboards/pages/07_geopolitica.py
Página 7 — Geopolítica
Petróleo, VIX, World Cup Risk Score (dados reais).
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402
from models.montecarlo.risk_score import calculate_risk_score  # noqa: E402

page_header("Geopolítica e Cenários Estratégicos", "Petróleo · VIX · World Cup Risk Score")


@st.cache_data(ttl=600)
def load_indicator(indicator_code: str, country_code: str | None = None) -> pd.DataFrame:
    with get_connection() as conn:
        if country_code:
            df = conn.execute(
                """
                SELECT period, value FROM fact_indicator_values
                WHERE indicator_code = ? AND country_code = ?
                ORDER BY period
                """,
                [indicator_code, country_code],
            ).df()
        else:
            df = conn.execute(
                """
                SELECT period, value FROM fact_indicator_values
                WHERE indicator_code = ?
                ORDER BY period
                """,
                [indicator_code],
            ).df()
    df["period"] = pd.to_datetime(df["period"])
    return df


@st.cache_data(ttl=600)
def load_risk_score():
    return calculate_risk_score()


risk_result = load_risk_score()

# ------------------------------------------------------------------
# KPIs
# ------------------------------------------------------------------
kpi_items = []

if risk_result["risk_score"] is not None:
    kpi_items.append(("World Cup Risk Score", f"{risk_result['risk_score']:.0f}/100", risk_result["classification"]))
else:
    kpi_items.append(("World Cup Risk Score", "—", None))

for code, label in [("WTI_CRUDE", "WTI (US$/bbl)"), ("BRENT_CRUDE", "Brent (US$/bbl)"), ("VIX", "VIX")]:
    df = load_indicator(code)
    if not df.empty:
        kpi_items.append((label, f"{df['value'].iloc[-1]:,.2f}", None))
    else:
        kpi_items.append((label, "—", None))

kpi_row(kpi_items)

st.markdown("###")

tabs = st.tabs(["Petróleo & Custos", "VIX & Volatilidade", "World Cup Risk Score"])

with tabs[0]:
    st.subheader("Petróleo (WTI/Brent) — referência para custos de transporte/aviação")
    fig = go.Figure()
    has_data = False
    for code, label in [("WTI_CRUDE", "WTI"), ("BRENT_CRUDE", "Brent")]:
        df = load_indicator(code)
        if not df.empty:
            fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=label))
            has_data = True
    fig.update_layout(title="Preço do petróleo (US$/bbl)")
    apply_theme(fig)
    if has_data:
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Petróleo — sem dados carregados")

    st.caption(
        "Custos operacionais de aviação são sensíveis ao preço do combustível "
        "(jet fuel), que tende a acompanhar o WTI/Brent com defasagem. "
        "Análise de sensibilidade detalhada pendente (página Aviação)."
    )

with tabs[1]:
    st.subheader("VIX — Volatilidade Implícita")
    df = load_indicator("VIX")
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name="VIX", line=dict(color="#E5534B")))
        fig.add_hline(y=20, line_dash="dot", line_color="#8B96A5", annotation_text="Nível histórico médio ≈ 20")
    fig.update_layout(title="VIX — série histórica")
    apply_theme(fig)
    if not df.empty:
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("VIX — sem dados carregados")

with tabs[2]:
    st.subheader("World Cup Risk Score")

    st.markdown(
        """
        Índice composto (0-100) combinando o **percentil histórico** dos
        seguintes componentes:

        - **VIX** (peso 40%): volatilidade implícita do mercado
        - **Choque no petróleo** (peso 35%): desvio do WTI vs. média móvel de 1 ano
        - **Volatilidade cambial** (peso 25%): volatilidade realizada do índice
          USD trade-weighted (FRED)

        Score mais alto = nível atual mais extremo em relação ao histórico
        observado de cada componente (não é uma previsão, é um termômetro
        de "quão fora do normal" estão as condições atuais).
        """
    )

    if risk_result["risk_score"] is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Risk Score", f"{risk_result['risk_score']:.1f} / 100", risk_result["classification"])
        with col2:
            st.metric("Completeness", f"{risk_result['completeness_pct']:.0f}%",
                      help="% do peso do índice baseado em componentes com dados suficientes")

        st.markdown("**Detalhamento por componente:**")
        rows = []
        for name, data in risk_result["components"].items():
            score = data["score"]
            rows.append({
                "Componente": name.replace("_", " ").title(),
                "Percentil Histórico": f"{score:.1f}" if score is not None else "—",
                "Detalhe": str(data["detail"]),
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        data_pending_notice("Risk Score — dados insuficientes (mínimo 30-252 observações por componente)")

    st.caption(
        "Classificação: <25 Baixo · 25-50 Moderado · 50-75 Elevado · >75 Crítico"
    )