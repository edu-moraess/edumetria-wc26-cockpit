"""
dashboards/pages/02_macroeconomia.py
Página 2 — Macroeconomia
PIB, Inflação, Juros, Desemprego, Câmbio — dados reais via FRED (EUA).
Canadá e México: extractors ainda pendentes (StatCan/Banxico macro).
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import HOST_COUNTRIES, COUNTRY_NAMES  # noqa: E402
from dashboards.components import page_header, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Macroeconomia", "PIB · Inflação · Juros · Desemprego · Câmbio")


@st.cache_data(ttl=600)
def load_indicator(country_code: str, indicator_code: str) -> pd.DataFrame:
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value
            FROM fact_indicator_values
            WHERE country_code = ? AND indicator_code = ?
            ORDER BY period
            """,
            [country_code, indicator_code],
        ).df()
    df["period"] = pd.to_datetime(df["period"])
    return df


country_code = st.selectbox(
    "País",
    HOST_COUNTRIES,
    format_func=lambda c: COUNTRY_NAMES[c],
)

if country_code != "USA":
    st.warning(
        f"⚠️ Dados macro de **{COUNTRY_NAMES[country_code]}** ainda não integrados "
        f"(extractors StatCan/Banxico para macro pendentes — apenas turismo "
        f"está coberto hoje). Selecione **Estados Unidos** para ver dados reais via FRED."
    )

tabs = st.tabs(["PIB", "Inflação", "Juros", "Desemprego", "Câmbio"])

INDICATOR_CONFIG = {
    "PIB Nominal": ("GDP_NOMINAL", "US$ bn"),
    "PIB Real": ("GDP_REAL", "índice encadeado"),
    "Inflação (CPI)": ("CPI", "índice"),
    "Juros (Fed Funds)": ("POLICY_RATE", "%"),
    "Desemprego": ("UNEMPLOYMENT_RATE", "%"),
    "Câmbio (índice USD)": ("FX_INDEX", "índice"),
}


def render_chart(tab, title, code, unit):
    with tab:
        st.subheader(f"{title} — {COUNTRY_NAMES[country_code]}")
        if country_code != "USA":
            data_pending_notice(f"{title} ({COUNTRY_NAMES[country_code]})")
            return

        df = load_indicator(country_code, code)
        if df.empty:
            data_pending_notice(f"{title} — sem dados carregados")
            return

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=title))
        fig.update_layout(title=f"{title} ({unit}) — fonte: FRED")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        last = df.iloc[-1]
        st.caption(f"Último valor: {last['value']:,.2f} ({last['period'].strftime('%b/%Y')})")


render_chart(tabs[0], "PIB Nominal", "GDP_NOMINAL", "US$ bn")
render_chart(tabs[1], "Inflação (CPI)", "CPI", "índice")
render_chart(tabs[2], "Juros (Fed Funds)", "POLICY_RATE", "%")
render_chart(tabs[3], "Desemprego", "UNEMPLOYMENT_RATE", "%")
render_chart(tabs[4], "Câmbio (índice USD)", "FX_INDEX", "índice")

st.markdown("###")
data_pending_notice(
    "Cenários (conservador/base/otimista/estresse) e projeções 2027-2035 — "
    "modelagem econométrica ainda pendente (models/econometric)"
)