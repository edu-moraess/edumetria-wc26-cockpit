"""
dashboards/pages/05_hotelaria.py
Página 5 — Hotelaria
ADR, RevPAR, Ocupação.
"""

import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402

page_header("Hotelaria", "ADR · RevPAR · Ocupação")

kpi_row([
    ("ADR Médio (pico)*", "US$ —", None),
    ("RevPAR (pico)*", "US$ —", None),
    ("Ocupação (pico)*", "—%", None),
    ("ADR vs. Baseline (variação)*", "—%", None),
])

st.markdown("###")

tabs = st.tabs(["Por Cidade-Sede", "Série Temporal", "Pipeline de Oferta"])

with tabs[0]:
    st.subheader("ADR e Ocupação por cidade-sede")

    st.markdown(
        """
        Esta seção apresentará **ADR (Average Daily Rate)** e **ocupação
        hoteleira** por cidade-sede, comparando o período da Copa com a
        sazonalidade histórica de cada mercado.

        **Por que ainda não está disponível:**

        A fonte de referência institucional para esses dados é o
        **STR Global / CoStar** — produto B2B pago, sem API pública.

        **Alternativas em avaliação:**
        - Relatórios trimestrais de **REITs hoteleiros** (Host Hotels,
          Marriott, Hilton — disponíveis via relatórios de resultados/IR)
          como proxy de tendência, não substituto direto de ADR/RevPAR local
        - **AirDNA** (foco em short-term rental, free tier limitado)

        **Onde isso será implementado:** `etl/extractors/hospitality_*.py`
        (ver roadmap — fase pós-MVP, condicionada a acesso STR Global via
        instituição parceira).
        """
    )
    data_pending_notice("Dados STR Global por cidade-sede (fonte paga)")

with tabs[1]:
    st.subheader("Evolução diária — ADR / RevPAR / Ocupação")

    st.markdown(
        """
        Esta seção apresentará a **série diária de alta frequência**
        durante o período do evento (junho-julho 2026), permitindo
        identificar o pico de demanda hoteleira.

        **Por que ainda não está disponível:** depende da mesma fonte de
        dados da aba anterior (STR Global).
        """
    )
    data_pending_notice("Série temporal de alta frequência — depende de STR Global")

with tabs[2]:
    st.subheader("Pipeline de oferta hoteleira 2026-2035")

    st.markdown(
        """
        Esta seção avaliará o **legado de infraestrutura hoteleira**:
        novos quartos planejados/construídos para o evento e sua absorção
        pelo mercado nos anos seguintes (componente "Infraestrutura" do
        WCLI).

        **Por que ainda não está disponível:**

        Requer dados de pipeline de construção hoteleira por cidade-sede
        — tipicamente disponíveis em relatórios de consultorias do setor
        (JLL, CBRE, Cushman & Wakefield) ou associações hoteleiras
        nacionais (AHLA nos EUA).

        **Onde isso será implementado:** alimenta `models/montecarlo/
        wcli_calculator.py` (componente "infraestrutura", hoje pendente).
        """
    )
    data_pending_notice("Pipeline de oferta hoteleira — alimenta componente Infraestrutura do WCLI")