"""
dashboards/pages/05_hotelaria.py
Página 5 — Hotelaria
"""

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Hotelaria", "Ocupação, ADR, RevPAR e pipeline de novos empreendimentos")

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

st.info("⏳ Dados de hotelaria em desenvolvimento — integração com STR/CoStar pendente")

st.subheader("Pipeline de Hotéis — Copa 2026")
st.markdown("""
- **Estados Unidos**: 45.000 quartos adicionais em construção
- **Canadá**: 8.000 quartos (Toronto, Vancouver)
- **México**: 12.000 quartos (CDMX, Guadalajara, Monterrey)
- **Ocupação esperada**: 85-95% durante jogos
""")
