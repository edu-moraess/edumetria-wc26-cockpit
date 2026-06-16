"""
dashboards/pages/03_turismo.py
Página 3 — Turismo Internacional
Agora todas as opções (CAN, MEX, USA) mostram apenas informativos,
sem exibir tabela ou dados numéricos.
"""

import sys
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import FIFA_BASELINE, COUNTRY_NAMES  # noqa: E402
from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402

page_header("Turismo Internacional", "Visitantes · Gastos · Permanência · Fluxos")

# ------------------------------------------------------------------
# KPIs — baseline global
# ------------------------------------------------------------------
kpi_items = [("Visitantes Totais (baseline FIFA 2026)", f"{FIFA_BASELINE['global']['visitors_total']:,}", None)]
kpi_row(kpi_items)

st.markdown("###")

# ------------------------------------------------------------------
# Seleção de país
# ------------------------------------------------------------------
country_code = st.selectbox(
    "País",
    ["CAN", "MEX", "USA"],
    format_func=lambda c: COUNTRY_NAMES.get(c, c),
)

tabs = st.tabs(["Série Histórica", "Setores Beneficiados (em desenvolvimento)", "Comparação CAN vs MEX"])

# ------------------------------------------------------------------
# Aba 1 — Série Histórica
# ------------------------------------------------------------------
with tabs[0]:
    st.subheader(f"Chegadas de turistas internacionais — {COUNTRY_NAMES[country_code]}")

    if country_code == "USA":
        data_pending_notice("Turismo EUA (NTTO) — download manual pendente")
    elif country_code == "CAN":
        data_pending_notice("Turismo Canadá (StatCan) — sem dados carregados")
    elif country_code == "MEX":
        data_pending_notice("Turismo México (Banxico) — sem dados carregados")

# ------------------------------------------------------------------
# Aba 2 — Setores Beneficiados
# ------------------------------------------------------------------
with tabs[1]:
    st.subheader("Decomposição setorial do gasto turístico")
    st.markdown(
        """
        Esta seção apresentará a **receita incremental por setor**
        (hotelaria, aviação, restaurantes, varejo, entretenimento),
        decompondo o gasto turístico total observado.

        **Por que ainda não está disponível:**
        - Requer modelo de Input-Output com multiplicadores setoriais
        - Gasto médio por visitante
        - Permanência média e padrão de consumo por setor
        """
    )
    data_pending_notice("Modelo Input-Output (multiplicadores setoriais)")

# ------------------------------------------------------------------
# Aba 3 — Comparação CAN vs MEX
# ------------------------------------------------------------------
with tabs[2]:
    st.subheader("Comparação: Canadá vs. México")
    data_pending_notice("Comparação CAN vs MEX — sem dados carregados")