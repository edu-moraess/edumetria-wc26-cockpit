"""
dashboards/pages/08_esg.py
Página 8 — ESG
Ambiental, Social, Governança.
"""

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, kpi_row, data_pending_notice  # noqa: E402

page_header("ESG", "Ambiental · Social · Governança")

kpi_row([
    ("Emissões Estimadas (CO2e)*", "— Mt", None),
    ("Compensação de Carbono (cobertura)*", "—%", None),
    ("Empregos com Capacitação*", "—", None),
    ("Score de Governança*", "—/100", None),
])

st.markdown("###")

tabs = st.tabs(["Ambiental", "Social", "Governança"])

with tabs[0]:
    st.subheader("Pegada Ambiental")

    st.markdown(
        """
        Esta seção apresentará a **decomposição de emissões** do evento
        (voos internacionais, energia em estádios, transporte local,
        construção de infraestrutura) e a cobertura de programas de
        compensação de carbono.

        **Por que ainda não está disponível:**

        Requer estimativas de pegada de carbono específicas do evento —
        tipicamente publicadas pela própria FIFA em relatórios de
        sustentabilidade, ou modeladas a partir de:
        - Volume de passageiros internacionais (página Turismo/Aviação)
        - Fatores de emissão por modal de transporte (ICAO, EPA)
        - Consumo energético de estádios (dados específicos por cidade-sede)

        **Onde isso será implementado:** `etl/extractors/esg_*.py` +
        `models/econometric/emissions_estimate.py` (fase pós-MVP).
        """
    )
    data_pending_notice("Estimativas de emissões — depende de dados de fluxo de passageiros + fatores de emissão")

with tabs[1]:
    st.subheader("Impacto Social")

    st.markdown(
        """
        Esta seção apresentará indicadores de **inclusão, emprego local e
        capacitação profissional** associados às obras e operação do evento.

        **Por que ainda não está disponível:**

        Esses indicadores tipicamente vêm de relatórios de impacto social
        de governos locais/organizadores — não há série temporal padronizada
        disponível via API.
        """
    )
    data_pending_notice("Indicadores sociais por cidade-sede — fonte a definir")

with tabs[2]:
    st.subheader("Governança")

    st.markdown(
        """
        Esta seção apresentará uma **avaliação qualitativa de governança**:
        transparência na gestão de contratos públicos, uso de recursos
        públicos e mecanismos de fiscalização.

        **Por que ainda não está disponível:**

        Governança não é um indicador numérico de série temporal — requer
        avaliação qualitativa estruturada (ex: scorecard baseado em
        critérios públicos de transparência, contratos publicados,
        auditorias do TCU/equivalentes em cada país).

        **Onde isso será implementado:** seção qualitativa do white paper
        institucional + scorecard manual (fase pós-MVP).
        """
    )
    data_pending_notice("Scorecard de governança — avaliação qualitativa, fase pós-MVP")