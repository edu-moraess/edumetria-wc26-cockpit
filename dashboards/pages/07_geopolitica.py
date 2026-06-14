"""
dashboards/pages/07_geopolitica.py
Página 7 — Geopolítica & Risk Monitor
World Cup Risk Score 2.0 (multicamadas) + Petróleo + VIX.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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


@st.cache_data(ttl=3600)
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


@st.cache_data(ttl=3600)
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
        | Financeira | 35% | VIX, MOVE Index, HY Spread, TED Spread |
        | Energética | 25% | WTI, Brent, Gás Natural (desvio vs. média 252d) |
        | Macroeconômica | 25% | Spread 10Y-2Y, 10Y-3M, Leading Index |
        | Geopolítica | 15% | *Geopolitical Risk Index — integração pendente* |

        **Limitação**: dimensão geopolítica (15%) depende do dataset
        Caldara & Iacoviello (2022) — não tem API gratuita automática.
        Peso redistribuído entre as 3 dimensões disponíveis até integração.
        """
    )

    if result["risk_score"] is not None:
        # Card principal do score
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
                      help="% do peso do índice coberto por dados disponíveis")
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
                "threshold": {
                    "line": {"color": color, "width": 3},
                    "thickness": 0.75,
                    "value": result["risk_score"],
                },
            },
        ))
        fig_gauge.update_layout(
            paper_bgcolor=bg,
            plot_bgcolor=bg,
            font={"family": font, "color": text},
            height=280,
            margin={"l": 20, "r": 20, "t": 40, "b": 20},
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("###")

        # Heatmap de contribuição marginal por dimensão
        st.subheader("Contribuição Marginal por Dimensão")

        dim_data = []
        for dim_name, dim in result["dimensions"].items():
            if dim["score"] is not None:
                marginal = dim["score"] * dim["weight"]
                dim_data.append({
                    "Dimensão":             dim["label"],
                    "Score (0-100)":        f"{dim['score']:.1f}",
                    "Peso":                 f"{dim['weight']*100:.0f}%",
                    "Contribuição Marginal": f"{marginal:.1f}",
                    "Completeness":         f"{dim['completeness']*100:.0f}%",
                })
            else:
                dim_data.append({
                    "Dimensão":             dim["label"],
                    "Score (0-100)":        "—",
                    "Peso":                 f"{dim['weight']*100:.0f}%",
                    "Contribuição Marginal": "—",
                    "Completeness":         "0%",
                })

        st.dataframe(pd.DataFrame(dim_data), hide_index=True, use_container_width=True)

        # Bar chart das contribuições
        dim_labels  = [d["Dimensão"] for d in dim_data if d["Score (0-100)"] != "—"]
        dim_scores  = [float(d["Score (0-100)"]) for d in dim_data if d["Score (0-100)"] != "—"]
        dim_contribs = [float(d["Contribuição Marginal"]) for d in dim_data if d["Contribuição Marginal"] != "—"]

        if dim_labels:
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=dim_labels, y=dim_scores,
                name="Score da Dimensão (0-100)",
                marker_color=[
                    positive if s < 25 else warning if s < 50
                    else "#E08E45" if s < 75 else negative
                    for s in dim_scores
                ],
            ))
            fig_bar.update_layout(title="Score por dimensão (0-100)")
            apply_theme(fig_bar)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("###")

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
                    if detail.get("deviation_pct") is not None:
                        detail_str += f" · Desvio: {detail['deviation_pct']:+.1f}%"
                    if detail.get("last_date"):
                        detail_str += f" · {detail['last_date']}"

                    rows.append({
                        "Componente": code,
                        "Percentil":  f"{score:.1f}" if score is not None else "excluído",
                        "Status":     detail.get("status", "—"),
                        "Detalhe":    detail_str,
                    })
                if rows:
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                else:
                    st.caption("Nenhum componente disponível.")

        st.caption(
            "Classificação: <25 Baixo · 25-50 Moderado · 50-75 Elevado · >75 Crítico · "
            "Metodologia: percentil histórico de cada componente na série disponível no banco."
        )
    else:
        data_pending_notice("Risk Score 2.0 — rode o pipeline ETL para carregar dados")

# ------------------------------------------------------------------
# ABA 2 — PETRÓLEO & ENERGIA
# ------------------------------------------------------------------
with tabs[1]:
    st.subheader("Petróleo & Energia — impacto nos custos do evento")

    # WTI e Brent no eixo principal (US$/bbl)
    fig = go.Figure()
    has_data = False
    for code, label, color in [
        ("WTI_CRUDE",   "WTI (US$/bbl)",   "#4C8BF5"),
        ("BRENT_CRUDE", "Brent (US$/bbl)", "#00C8FF"),
    ]:
        df = load_indicator(code)
        if not df.empty:
            fig.add_trace(go.Scatter(
                x=df["period"], y=df["value"], mode="lines",
                name=label, line=dict(color=color, width=1.5),
                yaxis="y1",
            ))
            has_data = True

    # Natural Gas no eixo secundário (US$/MMBTU — escala diferente)
    df_ng = load_indicator("NATURAL_GAS")
    if not df_ng.empty:
        fig.add_trace(go.Scatter(
            x=df_ng["period"], y=df_ng["value"], mode="lines",
            name="Gás Natural (US$/MMBTU)", line=dict(color="#FFB300", width=1.5, dash="dot"),
            yaxis="y2",
        ))
        has_data = True

    fig.update_layout(
        title="Commodities energéticas — petróleo (eixo esq.) e gás natural (eixo dir.)",
        yaxis=dict(title="US$/bbl",   side="left",  gridcolor=border),
        yaxis2=dict(title="US$/MMBTU", side="right", overlaying="y", showgrid=False),
    )
    apply_theme(fig)

    if has_data:
        st.plotly_chart(fig, use_container_width=True)
    else:
        data_pending_notice("Commodities energéticas — sem dados carregados")

    st.caption(
        "Eixo esquerdo: WTI e Brent (US$/bbl). "
        "Eixo direito: Gás Natural (US$/MMBTU — escala diferente). "
        "Relevância: jet fuel ∝ Brent/WTI; energia em estádios ∝ gás natural."
    )

# ------------------------------------------------------------------
# ABA 3 — VIX & STRESS FINANCEIRO
# ------------------------------------------------------------------
with tabs[2]:
    st.subheader("VIX, MOVE Index & Stress Financeiro")

    col1, col2 = st.columns(2)

    with col1:
        df_vix = load_indicator("VIX")
        fig = go.Figure()
        if not df_vix.empty:
            fig.add_trace(go.Scatter(
                x=df_vix["period"], y=df_vix["value"], mode="lines",
                line=dict(color=negative, width=1.5), name="VIX",
            ))
            fig.add_hline(y=20, line_dash="dot", line_color=secondary,
                          annotation_text="Média histórica ≈ 20")
            fig.add_hline(y=30, line_dash="dot", line_color=warning,
                          annotation_text="Nível de stress")
        fig.update_layout(title="VIX — Volatilidade Implícita S&P 500")
        apply_theme(fig)
        if not df_vix.empty:
            st.plotly_chart(fig, use_container_width=True)
        else:
            data_pending_notice("VIX — sem dados")

    with col2:
        df_hy = load_indicator("HY_SPREAD")
        fig2  = go.Figure()
        if not df_hy.empty:
            fig2.add_trace(go.Scatter(
                x=df_hy["period"], y=df_hy["value"], mode="lines",
                line=dict(color=warning, width=1.5), name="HY Spread",
            ))
            fig2.add_hline(y=4, line_dash="dot", line_color=secondary,
                           annotation_text="Nível normal ≈ 4%")
        fig2.update_layout(title="High Yield Spread — stress de crédito (%)")
        apply_theme(fig2)
        if not df_hy.empty:
            st.plotly_chart(fig2, use_container_width=True)
        else:
            data_pending_notice("HY Spread — sem dados (pode levar algumas atualizações)")

    df_ted = load_indicator("TED_SPREAD")
    if not df_ted.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df_ted["period"], y=df_ted["value"], mode="lines",
            line=dict(color=primary, width=1.5), name="TED Spread",
        ))
        fig3.add_hline(y=0.5, line_dash="dot", line_color=secondary,
                       annotation_text="Stress bancário histórico ≈ 0.5%")
        fig3.update_layout(title="TED Spread — stress interbancário (%)")
        apply_theme(fig3)
        st.plotly_chart(fig3, use_container_width=True)

# ------------------------------------------------------------------
# ABA 4 — YIELD CURVE
# ------------------------------------------------------------------
with tabs[3]:
    st.subheader("Yield Curve — Estrutura a Termo dos Juros EUA")

    df_10y   = load_indicator("TREASURY_10Y")
    df_2y    = load_indicator("TREASURY_2Y")
    df_3m    = load_indicator("TREASURY_3M")
    df_sp102 = load_indicator("YIELD_SPREAD_10Y2Y")
    df_sp103 = load_indicator("YIELD_SPREAD_10Y3M")

    fig = go.Figure()
    for df_s, label, color in [
        (df_3m,  "Treasury 3M",  secondary),
        (df_2y,  "Treasury 2Y",  "#00C8FF"),
        (df_10y, "Treasury 10Y", primary),
    ]:
        if not df_s.empty:
            fig.add_trace(go.Scatter(
                x=df_s["period"], y=df_s["value"], mode="lines",
                name=label, line=dict(color=color, width=1.5),
            ))
    fig.update_layout(title="Estrutura de juros EUA — Treasury 3M, 2Y e 10Y (%)")
    apply_theme(fig)
    if fig.data:
        st.plotly_chart(fig, use_container_width=True)

    # Spreads
    col1, col2 = st.columns(2)
    for col, df_sp, title, code in [
        (col1, df_sp102, "Spread 10Y–2Y", "10Y-2Y"),
        (col2, df_sp103, "Spread 10Y–3M", "10Y-3M"),
    ]:
        with col:
            fig_sp = go.Figure()
            if not df_sp.empty:
                fig_sp.add_trace(go.Scatter(
                    x=df_sp["period"], y=df_sp["value"],
                    mode="lines", fill="tozeroy",
                    fillcolor="rgba(76,139,245,0.10)",
                    line=dict(color=primary, width=1.5),
                    name=title,
                ))
                fig_sp.add_hline(y=0, line_dash="dash",
                                 line_color=negative,
                                 annotation_text="Inversão",
                                 annotation_font_color=negative)
                last = df_sp["value"].iloc[-1]
                last_date = df_sp["period"].iloc[-1].strftime("%b/%Y")
                color = negative if last < 0 else positive
                fig_sp.update_layout(title=f"{title}: {last:+.2f}% ({last_date})")
            apply_theme(fig_sp)
            if not df_sp.empty:
                st.plotly_chart(fig_sp, use_container_width=True)
            else:
                data_pending_notice(f"{title} — sem dados")