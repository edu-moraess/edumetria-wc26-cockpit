"""
dashboards/pages/10_recession_monitor.py — v3 CORRIGIDO
Página 10 — Recession Monitor

CORREÇÕES v3:
- Garantir que a lógica de carregamento não use cache antigo se o banco for atualizado
- Melhor tratamento de séries vazias/antigas
- Inclusão de indicadores de frescor na UI
"""

import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboards.components import page_header, apply_theme, data_pending_notice  # noqa: E402
from models.montecarlo.recession_monitor import calculate_recession_monitor  # noqa: E402
from database.connection import get_connection  # noqa: E402
from config import THEME  # noqa: E402

bg = THEME["background"]; surface = THEME["surface"]; border = THEME["border"]
primary = THEME["primary"]; secondary = THEME["secondary"]; text = THEME["text"]
positive = THEME["positive"]; negative = THEME["negative"]; warning = THEME["warning"]
font = THEME["font_family"]

page_header(
    "Recession Monitor",
    "Probabilidade de recessão nos EUA — principal cenário de estresse para a Copa 2026",
)


@st.cache_data(ttl=600)
def load_recession_monitor():
    return calculate_recession_monitor()


@st.cache_data(ttl=600)
def load_series(code: str, country: str = "USA") -> pd.DataFrame:
    with get_connection() as conn:
        df = conn.execute(
            "SELECT period, value FROM fact_indicator_values "
            "WHERE indicator_code = ? AND country_code = ? ORDER BY period",
            [code, country],
        ).df()
    if df.empty:
        return pd.DataFrame(columns=["period", "value"])
    df["period"] = pd.to_datetime(df["period"])
    return df.drop_duplicates(subset=["period"], keep="last")


result = load_recession_monitor()

# ------------------------------------------------------------------
# SCORE PRINCIPAL + SEMÁFORO
# ------------------------------------------------------------------
score = result["recession_score"]
label = result["classification"]

color_map = {
    "🟢 Baixo":    positive,
    "🟡 Moderado": warning,
    "🟠 Elevado":  "#E08E45",
    "🔴 Crítico":  negative,
}
color = color_map.get(label, secondary)

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    st.markdown(
        f"""
        <div style="background:{surface}; border:1px solid {border};
                    border-left:3px solid {color}; border-radius:4px;
                    padding:1rem; text-align:center;">
            <div style="color:{secondary}; font-size:0.68rem;
                        text-transform:uppercase; letter-spacing:0.10em;">
                Recession Score
            </div>
            <div style="color:{text}; font-size:2.2rem; font-weight:700;">
                {'%.1f' % score if score is not None else '—'}
            </div>
            <div style="font-size:1.2rem;">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.metric(
        "Completeness",
        f"{result['completeness_pct']:.0f}%",
        help="% do peso do índice coberto por indicadores disponíveis e recentes",
    )

with col3:
    st.markdown(
        f"""
        <div style="background:{surface}; border:1px solid {border};
                    border-radius:4px; padding:0.75rem 1rem;
                    font-size:0.78rem; color:{secondary}; line-height:1.7;">
            <strong style="color:{text};">Por que isso importa para a Copa 2026?</strong><br>
            Uma recessão nos EUA em 2025-2026 é o principal fator de estresse
            do cenário pessimista. O monitor combina 5 indicadores antecedente reais 
            para estimar a probabilidade deste cenário em tempo real.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("###")

# ------------------------------------------------------------------
# DETALHAMENTO POR COMPONENTE
# ------------------------------------------------------------------
st.subheader("Detalhamento por Indicador")

tabs = st.tabs([
    "Painel Resumo",
    "Sahm Rule",
    "Yield Spreads",
    "Leading Index",
    "Prob. Oficial (Fed NY)",
])

with tabs[0]:
    rows = []
    for name, comp in result["components"].items():
        data = comp["data"]
        prob = data["prob"]
        rows.append({
            "Indicador": name,
            "Prob. Recessão": f"{prob:.1f}%" if prob is not None else "—",
            "Valor Atual":   f"{data['current_value']:.2f}" if data.get("current_value") is not None else "—",
            "Sinal":         data.get("signal", "—"),
            "Última Data":   data.get("last_date", "—"),
        })

    df_summary = pd.DataFrame(rows)
    st.dataframe(df_summary, hide_index=True, use_container_width=True)

with tabs[1]:
    df = load_series("SAHM_RULE")
    if not df.empty:
        fig = go.Figure(go.Scatter(x=df["period"], y=df["value"], mode="lines", line=dict(color=primary, width=1.5)))
        fig.add_hline(y=0.5, line_dash="dash", line_color=negative, annotation_text="Threshold (0.5pp)")
        fig.update_layout(title="Sahm Rule — tempo real (pp)")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Sahm Rule — sem dados")

with tabs[2]:
    col1, col2 = st.columns(2)
    for col, code, title in [(col1, "YIELD_SPREAD_10Y2Y", "Spread 10Y-2Y (%)"), (col2, "YIELD_SPREAD_10Y3M", "Spread 10Y-3M (%)")]:
        with col:
            df = load_series(code)
            if not df.empty:
                fig = go.Figure(go.Scatter(x=df["period"], y=df["value"], mode="lines", fill="tozeroy", line=dict(color=primary, width=1.5)))
                fig.add_hline(y=0, line_dash="dash", line_color=negative)
                fig.update_layout(title=title)
                apply_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    df = load_series("LEADING_INDEX")
    if not df.empty:
        fig = go.Figure(go.Scatter(x=df["period"], y=df["value"], mode="lines", line=dict(color="#00D4AA", width=1.5)))
        fig.update_layout(title="Leading Economic Index — EUA")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    df = load_series("RECESSION_PROB")
    if not df.empty:
        fig = go.Figure(go.Scatter(x=df["period"], y=df["value"], mode="lines", fill="tozeroy", line=dict(color=negative, width=1.5)))
        fig.update_layout(title="Probabilidade de Recessão — Fed NY (%)")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
