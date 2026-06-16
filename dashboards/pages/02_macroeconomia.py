"""
dashboards/pages/02_macroeconomia.py
Página 2 — Macroeconomia
PIB, Inflação, Juros, Desemprego, Câmbio, Yield Spread — dados reais FRED (EUA).
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

page_header("Macroeconomia", "PIB · Inflação · Juros · Desemprego · Câmbio · Yield Spread")


@st.cache_data(ttl=3600)
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
    df = df.drop_duplicates(subset=["period"], keep="last")
    return df


country_code = st.selectbox(
    "País",
    HOST_COUNTRIES,
    format_func=lambda c: COUNTRY_NAMES[c],
)

if country_code != "USA":
    st.warning(
        f"⚠️ Dados macro de **{COUNTRY_NAMES[country_code]}** ainda não integrados. "
        f"Selecione **Estados Unidos** para ver dados reais via FRED."
    )

tabs = st.tabs(["PIB", "Inflação", "Juros & Yield Spread", "Desemprego", "Câmbio"])


def render_chart(tab, title: str, code: str, unit: str, color: str = "#4C8BF5"):
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
        fig.add_trace(go.Scatter(
            x=df["period"], y=df["value"], mode="lines",
            name=title, line=dict(color=color, width=1.5),
        ))
        fig.update_layout(title=f"{title} ({unit}) — fonte: FRED")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        last = df.iloc[-1]
        st.caption(
            f"Último valor: {last['value']:,.2f} "
            f"({last['period'].strftime('%b/%Y')})"
        )


render_chart(tabs[0], "PIB Nominal", "GDP_NOMINAL", "US$ bn")
render_chart(tabs[1], "Inflação (CPI)", "CPI", "índice", "#00C8FF")

# Aba 3 — Juros + Yield Spread (mais rica)
with tabs[2]:
    st.subheader(f"Juros & Yield Spread — {COUNTRY_NAMES[country_code]}")
    if country_code != "USA":
        data_pending_notice("Juros & Yield Spread — dados EUA apenas")
    else:
        df_fed   = load_indicator("USA", "POLICY_RATE")
        df_t10   = load_indicator("USA", "TREASURY_10Y")
        df_t2    = load_indicator("USA", "TREASURY_2Y")
        df_spread = load_indicator("USA", "YIELD_SPREAD_10Y2Y")

        # Gráfico 1 — Curva de juros (Fed Funds, 2Y, 10Y)
        fig1 = go.Figure()
        for df_s, label, color in [
            (df_fed,  "Fed Funds Rate",   "#4C8BF5"),
            (df_t2,   "Treasury 2Y",      "#00C8FF"),
            (df_t10,  "Treasury 10Y",     "#00D4AA"),
        ]:
            if not df_s.empty:
                fig1.add_trace(go.Scatter(
                    x=df_s["period"], y=df_s["value"],
                    mode="lines", name=label,
                    line=dict(color=color, width=1.5),
                ))
        fig1.update_layout(title="Estrutura de juros — Fed Funds, Treasury 2Y e 10Y (%)")
        apply_theme(fig1)
        if fig1.data:
            st.plotly_chart(fig1, use_container_width=True)

        # Gráfico 2 — Yield Spread (10Y - 2Y) com zona de inversão
        if not df_spread.empty:
            st.subheader("Yield Spread 10Y–2Y (EUA)")

            fig2 = go.Figure()

            # Área positiva (verde) e negativa (vermelha)
            fig2.add_trace(go.Scatter(
                x=df_spread["period"], y=df_spread["value"],
                mode="lines", name="Spread 10Y-2Y",
                line=dict(color="#4C8BF5", width=1.5),
                fill="tozeroy",
                fillcolor="rgba(76,139,245,0.12)",
            ))

            # Linha de zero
            fig2.add_hline(
                y=0,
                line_dash="dash",
                line_color="#FF4560",
                annotation_text="Inversão da curva (recessão histórica)",
                annotation_position="top left",
                annotation_font_color="#FF4560",
            )

            fig2.update_layout(
                title="Yield Spread 10Y–2Y (%) — inversão = sinal histórico de recessão",
                yaxis_title="Spread (%)",
            )
            apply_theme(fig2)
            st.plotly_chart(fig2, use_container_width=True)

            # KPI do spread atual
            last_spread = df_spread["value"].iloc[-1]
            last_date   = df_spread["period"].iloc[-1].strftime("%b/%Y")
            col1, col2 = st.columns(2)
            with col1:
                color = "#FF4560" if last_spread < 0 else "#00D4AA"
                st.markdown(
                    f"""
                    <div style="background:#111827; border:1px solid #1E2D45;
                                border-left:3px solid {color}; border-radius:4px;
                                padding:0.75rem 1rem;">
                        <div style="color:#6B7A99; font-size:0.68rem;
                                    text-transform:uppercase; letter-spacing:0.10em;">
                            Yield Spread Atual ({last_date})
                        </div>
                        <div style="color:{color}; font-size:1.4rem; font-weight:700;">
                            {last_spread:+.2f}%
                        </div>
                        <div style="color:{color}; font-size:0.75rem;">
                            {'⚠ Curva invertida — sinal histórico de recessão' if last_spread < 0
                             else '✓ Curva normal — sem sinal imediato de recessão'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    """
                    <div style="background:#111827; border:1px solid #1E2D45;
                                border-radius:4px; padding:0.75rem 1rem;
                                font-size:0.75rem; color:#6B7A99; line-height:1.6;">
                        <strong style="color:#E2E8F0;">Por que isso importa para a Copa?</strong><br>
                        Uma inversão sustentada (spread &lt; 0) historicamente
                        precede recessões nos EUA em 12-18 meses.
                        Uma recessão em 2025-2026 é o principal fator de
                        estresse do cenário pessimista — afeta consumo,
                        turismo e receita fiscal do evento.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            data_pending_notice("Yield Spread — sem dados (rode o pipeline ETL)")

render_chart(tabs[3], "Desemprego", "UNEMPLOYMENT_RATE", "%", "#A78BFA")
render_chart(tabs[4], "Câmbio (índice USD)", "FX_INDEX", "índice", "#FFB300")

st.markdown("###")
data_pending_notice(
    "Cenários (conservador/base/otimista/estresse) e projeções 2027-2035 — "
    "modelagem econométrica pendente (models/econometric)"
)