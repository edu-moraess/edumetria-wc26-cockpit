"""
dashboards/pages/04_aviacao.py
Página 4 — Aviação
Rotas, Passageiros, Assentos.
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
    st.subheader("Capacidade adicional por hub aeroportuário (cidades-sede)")

    st.markdown(
        """
        Esta seção apresentará a **capacidade adicional de assentos e rotas**
        por aeroporto-sede durante o período da Copa.

        **Por que ainda não está disponível:**

        Dados de capacidade aérea (rotas, assentos ofertados, frequências)
        não têm fonte pública gratuita com API REST. As fontes de referência
        são **OAG** e **IATA**, ambas pagas (B2B).

        **Alternativas em avaliação:**
        - Dados de aeroportos via **OpenFlights** (estático, desatualizado)
        - Estatísticas da **FAA** (EUA) — possível via download manual
        - **Transport Canada** / **AFAC México** — estatísticas oficiais nacionais

        **Onde isso será implementado:** `etl/extractors/aviation_*.py`
        (ver roadmap do projeto — fase pós-MVP).
        """
    )
    data_pending_notice("Dados de capacidade aérea (OAG/IATA — fontes pagas)")

with tabs[1]:
    st.subheader("Sazonalidade de passageiros — junho/julho 2026")

    st.markdown(
        """
        Esta seção apresentará a **curva diária de chegada/saída de
        passageiros** durante o evento, permitindo identificar picos de
        demanda por aeroporto-sede.

        **Por que ainda não está disponível:** depende da mesma fonte de
        dados de capacidade aérea (ver aba anterior).
        """
    )
    data_pending_notice("Curva de sazonalidade de passageiros — depende de dados de capacidade")

with tabs[2]:
    st.subheader("Custos operacionais — sensibilidade ao petróleo (dados reais)")

    @st.cache_data(ttl=600)
    def load_oil_series(indicator_code: str) -> pd.DataFrame:
        with get_connection() as conn:
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

    df = load_oil_series("WTI_CRUDE")

    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name="WTI (US$/bbl)"))
        fig.update_layout(title="WTI — proxy para custo de jet fuel (série real)")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        last = df["value"].iloc[-1]
        st.caption(
            f"WTI atual: US$ {last:,.2f}/bbl. Jet fuel tende a acompanhar o "
            f"WTI/Brent com defasagem — ver página Geopolítica para contexto "
            f"completo (World Cup Risk Score)."
        )

        st.markdown(
            """
            **O que falta para a análise completa de sensibilidade:**

            - Participação do combustível no custo operacional total (CASK)
              por companhia aérea/região
            - Elasticidade histórica entre WTI e tarifas (jet fuel surcharge)
            - Projeção de cenários de custo por faixa de preço do petróleo

            **Onde isso será implementado:** `models/econometric/`
            (análise de sensibilidade fuel-cost).
            """
        )
        data_pending_notice("Modelo de sensibilidade de custos (CASK x WTI)")
    else:
        data_pending_notice("WTI — sem dados carregados")