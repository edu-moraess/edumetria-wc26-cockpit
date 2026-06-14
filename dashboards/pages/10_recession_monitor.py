"""
dashboards/pages/10_recession_monitor.py
Página 10 — Recession Monitor
Probabilidade de recessão nos EUA 2025-2026 — relevância para a Copa.
"""

import sys
from pathlib import Path

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


@st.cache_data(ttl=3600)
def load_recession_monitor():
    return calculate_recession_monitor()


@st.cache_data(ttl=3600)
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
                {'%.1f' % score if score else '—'}
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
        help="% do peso do índice coberto por indicadores disponíveis",
    )

with col3:
    st.markdown(
        f"""
        <div style="background:{surface}; border:1px solid {border};
                    border-radius:4px; padding:0.75rem 1rem;
                    font-size:0.78rem; color:{secondary}; line-height:1.7;">
            <strong style="color:{text};">Por que isso importa para a Copa 2026?</strong><br>
            Uma recessão nos EUA em 2025-2026 é o principal fator de estresse
            do cenário pessimista: reduz turismo corporativo, comprime consumo,
            afeta receita de patrocinadores e pode pressionar gastos públicos
            comprometidos com o evento. O Recession Monitor combina 5 indicadores
            antecedentes para estimar a probabilidade deste cenário.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("###")

# ------------------------------------------------------------------
# GAUGE
# ------------------------------------------------------------------
if score is not None:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Probabilidade de Recessão — Score Composto (0-100)",
               "font": {"size": 13, "color": text}},
        number={"suffix": "", "font": {"size": 36, "color": text, "family": font}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"color": secondary, "size": 10}},
            "bar":  {"color": color, "thickness": 0.25},
            "bgcolor": surface,
            "bordercolor": border,
            "steps": [
                {"range": [0,  15], "color": "rgba(0,212,170,0.15)"},
                {"range": [15, 35], "color": "rgba(255,179,0,0.15)"},
                {"range": [35, 60], "color": "rgba(224,142,69,0.15)"},
                {"range": [60,100], "color": "rgba(255,69,96,0.15)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.75,
                "value": score,
            },
        },
    ))
    fig_gauge.update_layout(
        paper_bgcolor=bg, plot_bgcolor=bg,
        font={"family": font, "color": text},
        height=260,
        margin={"l": 20, "r": 20, "t": 40, "b": 10},
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

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
            "Peso":          f"{comp['weight']*100:.0f}%",
        })

    df_summary = pd.DataFrame(rows)
    st.dataframe(df_summary, hide_index=True, use_container_width=True)

    st.caption(
        "Score composto = média ponderada das probabilidades individuais. "
        "Classificação: <15 Baixo · 15-35 Moderado · 35-60 Elevado · >60 Crítico."
    )

with tabs[1]:
    st.subheader("Sahm Rule")
    st.markdown(
        """
        **Definição**: diferença entre a taxa de desemprego média dos últimos 3 meses
        e o mínimo dos últimos 12 meses. Valor ≥ 0.5pp → recessão em curso.

        **Criada por**: Claudia Sahm (2019), então economista do Federal Reserve.
        Regra empiricamente robusta — não gerou falsos positivos nas últimas 5 recessões.

        **Limitação**: indicador coincidente, não antecedente — sinaliza recessão
        que já começou, não previamente.

        *Referência: Sahm, C. (2019). "Direct Stimulus Payments to Individuals."
        The Hamilton Project.*
        """
    )
    df = load_series("SAHM_RULE")
    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["period"], y=df["value"], mode="lines",
            line=dict(color=primary, width=1.5), name="Sahm Rule",
        ))
        fig.add_hline(y=0.5, line_dash="dash", line_color=negative,
                      annotation_text="Threshold recessão (0.5pp)",
                      annotation_font_color=negative)
        fig.update_layout(title="Sahm Rule — tempo real (pp)")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Sahm Rule — rode o pipeline ETL")

with tabs[2]:
    st.subheader("Yield Spreads — 10Y-2Y e 10Y-3M")
    st.markdown(
        """
        **10Y-2Y**: spread mais popular, amplamente monitorado.
        **10Y-3M**: preferido pelo Fed NY para modelos de previsão de recessão
        (Estrella & Mishkin, 1998) — maior poder preditivo empiricamente.

        Inversão (spread < 0) historicamente precede recessões em 12-18 meses.
        """
    )
    col1, col2 = st.columns(2)
    for col, code, title in [
        (col1, "YIELD_SPREAD_10Y2Y", "Spread 10Y-2Y (%)"),
        (col2, "YIELD_SPREAD_10Y3M", "Spread 10Y-3M (%)"),
    ]:
        with col:
            df = load_series(code)
            fig = go.Figure()
            if not df.empty:
                fig.add_trace(go.Scatter(
                    x=df["period"], y=df["value"], mode="lines",
                    fill="tozeroy",
                    fillcolor="rgba(76,139,245,0.10)",
                    line=dict(color=primary, width=1.5),
                    name=title,
                ))
                fig.add_hline(y=0, line_dash="dash", line_color=negative,
                              annotation_text="Inversão",
                              annotation_font_color=negative)
                last = df["value"].iloc[-1]
                fig.update_layout(title=f"{title}: {last:+.2f}%")
            apply_theme(fig)
            if not df.empty:
                st.plotly_chart(fig, use_container_width=True)
            else:
                data_pending_notice(f"{title}")

with tabs[3]:
    st.subheader("Leading Economic Index (Conference Board)")
    st.markdown(
        """
        Composto por 6 indicadores antecedentes: horas trabalhadas na manufatura,
        pedidos de seguro-desemprego, ordens de manufatura, ISM novos pedidos,
        spread de juros e expectativas dos consumidores.

        **Sinal de recessão**: declínio em 3 meses consecutivos.
        """
    )
    df = load_series("LEADING_INDEX")
    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["period"], y=df["value"], mode="lines",
            line=dict(color="#00D4AA", width=1.5), name="Leading Index",
        ))
        fig.update_layout(title="Leading Economic Index — EUA")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Leading Index — rode o pipeline ETL")

with tabs[4]:
    st.subheader("Probabilidade Oficial — Fed NY (modelo probit)")
    st.markdown(
        """
        Modelo probit do Federal Reserve Bank of New York baseado no spread
        Treasury 10Y-3M. Estimado mensalmente; interpretado como probabilidade
        de recessão nos próximos 12 meses.

        *Referência: Estrella, A. & Mishkin, F.S. (1998). "Predicting U.S.
        Recessions: Financial Variables as Leading Indicators."
        Review of Economics and Statistics 80(1): 45-61.*
        """
    )
    df = load_series("RECESSION_PROB")
    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["period"], y=df["value"], mode="lines",
            fill="tozeroy",
            fillcolor="rgba(255,69,96,0.10)",
            line=dict(color=negative, width=1.5),
            name="Prob. Recessão Fed NY (%)",
        ))
        fig.add_hline(y=30, line_dash="dot", line_color=warning,
                      annotation_text="30% — threshold histórico de alerta")
        fig.update_layout(
            title="Probabilidade de Recessão — Fed NY (%)",
            yaxis_title="%",
        )
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Prob. Recessão Fed NY — rode o pipeline ETL")