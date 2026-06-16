"""
dashboards/pages/07_geopolitica.py — v3 CORRIGIDO
World Cup Risk Score 2.0 (multicamadas) + Petróleo + VIX + Stress Financeiro.

CORREÇÕES v3:
- REMOVIDO TED Spread (descontinuado) da UI e documentação
- ADICIONADO SOFR (Secured Overnight Financing Rate)
- Alinhamento com Risk Score v3 (validação de frescor)
- Melhor tratamento de dados ausentes/desatualizados
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
from models.montecarlo.risk_score_v2 import calculate_risk_score_v2  # noqa: E402

# Variáveis de tema
from config import THEME  # noqa: E402
bg = THEME["background"]; surface = THEME["surface"]; border = THEME["border"]
primary = THEME["primary"]; secondary = THEME["secondary"]; text = THEME["text"]
positive = THEME["positive"]; negative = THEME["negative"]; warning = THEME["warning"]
font = THEME["font_family"]

page_header("Geopolítica & Risk Monitor", "World Cup Risk Score 2.0 · Petróleo · VIX · Stress Financeiro")


@st.cache_data(ttl=600)
def load_indicator(indicator_code: str) -> pd.DataFrame:
    with get_connection() as conn:
        df = conn.execute(
            "SELECT period, value FROM fact_indicator_values "
            "WHERE indicator_code = ? ORDER BY period",
            [indicator_code],
        ).df()
    if df.empty:
        return pd.DataFrame(columns=["period", "value"])
    df["period"] = pd.to_datetime(df["period"])
    df = df.drop_duplicates(subset=["period"], keep="last")
    return df


@st.cache_data(ttl=600)
def load_risk_score():
    return calculate_risk_score_v2()


result = load_risk_score()

# ------------------------------------------------------------------
# KPIs
# ------------------------------------------------------------------
kpi_items = []

if result["risk_score"] is not None:
    kpi_items.append(("WC Risk Score 2.0", f"{result['risk_score']:.0f}/100", result["classification"]))
else:
    kpi_items.append(("WC Risk Score 2.0", "—", None))

for code, label in [
    ("WTI_CRUDE",  "WTI (US$/bbl)"),
    ("BRENT_CRUDE","Brent (US$/bbl)"),
    ("VIX",        "VIX"),
    ("HY_SPREAD",  "HY Spread (%)"),
]:
    df = load_indicator(code)
    if not df.empty:
        kpi_items.append((label, f"{df['value'].iloc[-1]:,.2f}", None))
    else:
        kpi_items.append((label, "—", None))

kpi_row(kpi_items)

st.markdown("###")

tabs = st.tabs([
    "Risk Score 2.0",
    "Petróleo & Energia",
    "VIX & Stress Financeiro",
    "Yield Curve",
])

# ------------------------------------------------------------------
# ABA 1 — RISK SCORE 2.0
# ------------------------------------------------------------------
with tabs[0]:
    st.subheader("World Cup Risk Score 2.0 — Multicamadas")

    st.markdown(
        """
        Framework multicamadas combinando **4 dimensões de risco**,
        cada uma calculada via percentil histórico dos componentes disponíveis.
        Score final = média ponderada das dimensões (0-100, onde 100 = risco máximo histórico).

        | Dimensão | Peso | Componentes |
        |---|---|---|
        | Financeira | 35% | VIX, MOVE Index, HY Spread, SOFR |
        | Energética | 25% | WTI, Brent, Gás Natural (desvio vs. média 252d) |
        | Macroeconômica | 25% | Spread 10Y-2Y, 10Y-3M, Leading Index |
        | Geopolítica | 15% | *Geopolitical Risk Index — integração pendente* |

        **Nota**: O **SOFR** substituiu o TED Spread (descontinuado em 2023) como proxy de stress bancário.
        """
    )

    if result["risk_score"] is not None:
        color_map = {"Baixo": positive, "Moderado": warning,
                     "Elevado": "#E08E45", "Crítico": negative}
        color = color_map.get(result["classification"], secondary)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div style="background:{surface}; border:1px solid {border};
                            border-left:3px solid {color}; border-radius:4px;
                            padding:0.75rem 1rem;">
                    <div style="color:{secondary}; font-size:0.68rem;
                                text-transform:uppercase; letter-spacing:0.10em;">
                        Risk Score 2.0
                    </div>
                    <div style="color:{text}; font-size:1.8rem; font-weight:700;">
                        {result['risk_score']:.1f}<span style="font-size:1rem; color:{secondary};"> / 100</span>
                    </div>
                    <div style="color:{color}; font-size:0.85rem; font-weight:600;">
                        ⚠ {result['classification']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.metric("Completeness", f"{result['completeness_pct']:.0f}%",
                      help="% do peso do índice coberto por dados reais e recentes")
        with col3:
            n_dims = sum(1 for d in result["dimensions"].values() if d["score"] is not None)
            st.metric("Dimensões ativas", f"{n_dims}/4")

        st.markdown("###")

        # Gauge chart do score
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=result["risk_score"],
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "World Cup Risk Score 2.0", "font": {"size": 13, "color": text}},
            number={"font": {"size": 36, "color": text, "family": font}},
            gauge={
                "axis": {"range": [0, 100], "tickfont": {"color": secondary, "size": 10}},
                "bar":  {"color": color, "thickness": 0.25},
                "bgcolor": surface,
                "bordercolor": border,
                "steps": [
                    {"range": [0, 25],   "color": "rgba(0,212,170,0.15)"},
                    {"range": [25, 50],  "color": "rgba(255,179,0,0.15)"},
                    {"range": [50, 75],  "color": "rgba(224,142,69,0.15)"},
                    {"range": [75, 100], "color": "rgba(255,69,96,0.15)"},
                ],
            },
        ))
        fig_gauge.update_layout(paper_bgcolor=bg, plot_bgcolor=bg, height=280, margin={"l": 20, "r": 20, "t": 40, "b": 20})
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Detalhamento por componente
        with st.expander("🔍 Detalhamento por componente"):
            for dim_name, dim in result["dimensions"].items():
                st.markdown(f"**{dim['label']}**")
                rows = []
                for code, comp in dim.get("components", {}).items():
                    detail = comp["detail"]
                    score  = comp["score"]
                    detail_str = ""
                    if detail.get("current_value") is not None:
                        detail_str += f"Atual: {detail['current_value']:.2f}"
                    if detail.get("last_date"):
                        detail_str += f" · Data: {detail['last_date']}"
                    
                    rows.append({
                        "Componente": code,
                        "Percentil":  f"{score:.1f}" if score is not None else "excluído",
                        "Status":     detail.get("status", "—"),
                        "Detalhe":    detail_str,
                    })
                if rows:
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        data_pending_notice("Risk Score 2.0 — rode o pipeline ETL para carregar dados reais")

# ------------------------------------------------------------------
# ABA 2 — PETRÓLEO & ENERGIA
# ------------------------------------------------------------------
with tabs[1]:
    st.subheader("Petróleo & Energia — impacto nos custos do evento")
    fig = go.Figure()
    has_data = False
    for code, label, color in [("WTI_CRUDE", "WTI (US$/bbl)", "#4C8BF5"), ("BRENT_CRUDE", "Brent (US$/bbl)", "#00C8FF")]:
        df = load_indicator(code)
        if not df.empty:
            fig.add_trace(go.Scatter(x=df["period"], y=df["value"], mode="lines", name=label, line=dict(color=color, width=1.5)))
            has_data = True
    
    fig.update_layout(title="Commodities energéticas (US$/bbl)")
    apply_theme(fig)
    if has_data:
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Petróleo — sem dados carregados")

# ------------------------------------------------------------------
# ABA 3 — VIX & STRESS FINANCEIRO
# ------------------------------------------------------------------
with tabs[2]:
    st.subheader("VIX, MOVE Index & Stress Financeiro")
    col1, col2 = st.columns(2)
    with col1:
        df_vix = load_indicator("VIX")
        if not df_vix.empty:
            fig = go.Figure(go.Scatter(x=df_vix["period"], y=df_vix["value"], mode="lines", line=dict(color=negative, width=1.5), name="VIX"))
            fig.update_layout(title="VIX — Volatilidade Implícita")
            apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        df_sofr = load_indicator("SOFR_RATE")
        if not df_sofr.empty:
            fig = go.Figure(go.Scatter(x=df_sofr["period"], y=df_sofr["value"], mode="lines", line=dict(color=primary, width=1.5), name="SOFR"))
            fig.update_layout(title="SOFR — Stress Interbancário (%)")
            apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
    
    df_hy = load_indicator("HY_SPREAD")
    if not df_hy.empty:
        fig = go.Figure(go.Scatter(x=df_hy["period"], y=df_hy["value"], mode="lines", line=dict(color=warning, width=1.5), name="HY Spread"))
        fig.update_layout(title="High Yield Spread — Stress de Crédito (%)")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# ABA 4 — YIELD CURVE
# ------------------------------------------------------------------
with tabs[3]:
    st.subheader("Yield Curve Spreads — EUA")
    col1, col2 = st.columns(2)
    for col, code, title in [(col1, "YIELD_SPREAD_10Y2Y", "Spread 10Y-2Y (%)"), (col2, "YIELD_SPREAD_10Y3M", "Spread 10Y-3M (%)")]:
        with col:
            df = load_indicator(code)
            if not df.empty:
                fig = go.Figure(go.Scatter(x=df["period"], y=df["value"], mode="lines", fill="tozeroy", line=dict(color=primary, width=1.5)))
                fig.add_hline(y=0, line_dash="dash", line_color=negative)
                fig.update_layout(title=title)
                apply_theme(fig)
                st.plotly_chart(fig, use_container_width=True)
