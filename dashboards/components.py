"""
dashboards/components.py
Componentes de UI reutilizáveis entre páginas: cards de KPI, header de
página e wrapper de gráfico Plotly com tema institucional aplicado.

IMPORTANTE: nunca usar `**PLOTLY_BASE` dentro de `fig.update_layout()`
quando a figura contém subplots — isso provoca conflito de kwargs.
Em vez disso, aplicar o tema via `apply_theme()`, que usa apenas chaves
de alto nível seguras para subplots.
"""

import streamlit as st
import plotly.graph_objects as go

from config import THEME, PLOTLY_BASE


def get_layout_theme() -> dict:
    """Retorna apenas as chaves de layout seguras para update_layout,
    mesmo em figuras com subplots (evita o bug de **PLOTLY_BASE)."""
    return {
        "template": PLOTLY_BASE["template"],
        "paper_bgcolor": PLOTLY_BASE["paper_bgcolor"],
        "plot_bgcolor": PLOTLY_BASE["plot_bgcolor"],
        "font": PLOTLY_BASE["font"],
    }


def apply_theme(fig: go.Figure) -> go.Figure:
    """Aplica o tema institucional a uma figura Plotly (subplot-safe)."""
    fig.update_layout(**get_layout_theme())
    fig.update_xaxes(gridcolor=THEME["grid"], zerolinecolor=THEME["grid"])
    fig.update_yaxes(gridcolor=THEME["grid"], zerolinecolor=THEME["grid"])
    return fig


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<span style='color:{THEME['secondary']}'>{subtitle}</span>",
                     unsafe_allow_html=True)
    st.markdown("---")


def kpi_card(label: str, value: str, delta: str | None = None):
    delta_html = ""
    if delta is not None:
        color = THEME["positive"] if not delta.startswith("-") else THEME["negative"]
        delta_html = f"<div style='color:{color}; font-size:0.8rem;'>{delta}</div>"

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items: list[tuple[str, str, str | None]]):
    """items: lista de (label, value, delta_opcional)"""
    cols = st.columns(len(items))
    for col, (label, value, delta) in zip(cols, items):
        with col:
            kpi_card(label, value, delta)


def data_pending_notice(section: str):
    """Placeholder padronizado para seções aguardando pipeline ETL / modelos."""
    st.info(
        f"📊 **{section}** — dados e modelos a integrar via pipeline ETL "
        f"(ver `etl/` e `models/`). Estrutura de visualização já implementada; "
        f"populando com séries reais e projeções nas próximas entregas.",
        icon="🛠️",
    )
