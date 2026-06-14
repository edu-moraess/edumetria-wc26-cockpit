"""
dashboards/pages/04_aviacao.py
Página 4 — Aviação
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Aviação", "Rotas · Passageiros · Assentos")

kpi_row([
    ("Rotas Adicionais*", "—", None),
    ("Passageiros Incrementais*", "—", None),
    ("Assentos Ofertados (variação)*", "—%", None),
    ("Load Factor (pico)*", "—%", None),
])

st.markdown("###")

tabs = st.tabs(["Capacidade & Rotas", "Sazonalidade", "Custos Operacionais (Petróleo)"])

with tabs[0]:
    st.subheader("Capacidade adicional por hub aeroportuário")
    st.markdown(
        """
        Esta seção apresentará a **capacidade adicional de assentos e rotas**
        por aeroporto-sede durante o período da Copa.

        **Por que ainda não está disponível:**
        Dados de capacidade aérea (rotas, assentos ofertados, frequências)
        não têm fonte pública gratuita com API REST. As fontes de referência
        são **OAG** e **IATA**, ambas pagas (B2B).

        **Alternativas em avaliação:**
        - Dados da **FAA** (EUA) — estatísticas oficiais via download manual
        - **Transport Canada** / **AFAC México** — estatísticas nacionais

        **Onde isso será implementado:** `etl/extractors/aviation_*.py`
        (roadmap — fase pós-MVP).
        """
    )
    data_pending_notice("Dados de capacidade aérea (OAG/IATA — fontes pagas)")

with tabs[1]:
    st.subheader("Sazonalidade de passageiros — junho/julho 2026")
    st.markdown(
        """
        Esta seção apresentará a **curva diária de chegada/saída de
        passageiros** durante o evento, por aeroporto-sede.

        **Por que ainda não está disponível:** depende da mesma fonte
        de dados de capacidade aérea (ver aba anterior).
        """
    )
    data_pending_notice("Curva de sazonalidade — depende de dados de capacidade")

with tabs[2]:
    st.subheader("Custos operacionais — sensibilidade ao petróleo (dados reais)")

    @st.cache_data(ttl=600)
    def load_oil(code: str) -> "pd.DataFrame":
        import pandas as pd
        with get_connection() as conn:
            df = conn.execute(
                "SELECT period, value FROM fact_indicator_values "
                "WHERE indicator_code = ? ORDER BY period",
                [code],
            ).df()
        df["period"] = pd.to_datetime(df["period"])
        return df

    import pandas as pd

    df_wti = load_oil("WTI_CRUDE")

    if not df_wti.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_wti["period"], y=df_wti["value"],
            mode="lines", name="WTI (US$/bbl)",
            line=dict(color="#4C8BF5"),
        ))
        fig.update_layout(title="WTI — proxy para custo de jet fuel (série real)")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        last = df_wti["value"].iloc[-1]
        last_date = df_wti["period"].iloc[-1].strftime("%b/%Y")
        st.caption(
            f"WTI atual: US$ {last:,.2f}/bbl ({last_date}). "
            f"Jet fuel acompanha WTI/Brent com defasagem — "
            f"ver página Geopolítica para contexto completo."
        )

        st.markdown(
            """
            **O que falta para análise completa:**
            - Participação do combustível no custo operacional (CASK) por companhia/região
            - Elasticidade histórica entre WTI e tarifas (jet fuel surcharge)
            - Projeção de cenários de custo por faixa de preço do petróleo

            **Onde isso será implementado:** `models/econometric/`
            (análise de sensibilidade fuel-cost).
            """
        )
        data_pending_notice("Modelo de sensibilidade de custos (CASK x WTI)")
    else:
        data_pending_notice("WTI — sem dados carregados")