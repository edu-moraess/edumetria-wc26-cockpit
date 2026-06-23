"""
dashboards/pages/08_esg.py
Página 8 — ESG
"""

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("ESG", "Environmental, Social, Governance — Copa 2026")

has_data = False
try:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
        has_data = count > 0
except:
    pass

if not has_data:
    st.warning("⚠️ **Sem dados disponíveis**")
    st.info("Clique em **'🎲 Criar dados de demonstração'** na sidebar.")
    st.stop()

st.info("⏳ Dados ESG em desenvolvimento — integração com MSCI/Sustainalytics pendente")

st.subheader("Compromissos FIFA 2026")
st.markdown("""
- **Carbono neutro**: compensação de 100% das emissões
- **Estádios sustentáveis**: certificação LEED/BREEAM
- **Mobilidade**: transporte público prioritário
- **Resíduos**: zero waste nos estádios
""")
