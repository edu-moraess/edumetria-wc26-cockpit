"""
dashboards/components.py
Componentes de UI reutilizáveis — KPI cards, page header, tema Plotly.
VERSÃO v4: Sem HTML mal formatado, usando componentes nativos Streamlit
"""

import streamlit as st
import plotly.graph_objects as go

from config import THEME, PLOTLY_BASE, SERIES_PALETTE

# Extrai variáveis para evitar escape de aspas em f-strings
bg = THEME["background"]
surface = THEME["surface"]
surface_alt = THEME["surface_alt"]
border = THEME["border"]
primary = THEME["primary"]
secondary = THEME["secondary"]
text = THEME["text"]
text_muted = THEME["text_muted"]
positive = THEME["positive"]
negative = THEME["negative"]
warning = THEME["warning"]
font = THEME["font_family"]


def get_layout_theme() -> dict:
    return {
        "template": PLOTLY_BASE["template"],
        "paper_bgcolor": PLOTLY_BASE["paper_bgcolor"],
        "plot_bgcolor": PLOTLY_BASE["plot_bgcolor"],
        "font": PLOTLY_BASE["font"],
        "title_font": {
            "family": font,
            "color": text,
            "size": 13,
        },
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": border,
            "borderwidth": 1,
            "font": {"size": 11, "color": secondary},
        },
        "hoverlabel": {
            "bgcolor": surface_alt,
            "bordercolor": border,
            "font": {"family": font, "size": 11, "color": text},
        },
        "margin": {"l": 48, "r": 24, "t": 48, "b": 40},
    }


def apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(**get_layout_theme())
    fig.update_xaxes(
        gridcolor=border,
        zerolinecolor=border,
        tickfont={"size": 10, "color": secondary},
        title_font={"size": 11, "color": secondary},
        showspikes=True,
        spikecolor=border,
        spikethickness=1,
    )
    fig.update_yaxes(
        gridcolor=border,
        zerolinecolor=border,
        tickfont={"size": 10, "color": secondary},
        title_font={"size": 11, "color": secondary},
        showspikes=True,
        spikecolor=border,
        spikethickness=1,
    )
    return fig


def page_header(title: str, subtitle: str = ""):
    """Header de página usando componentes nativos Streamlit (sem HTML)."""
    st.title(title)
    if subtitle:
        st.caption(subtitle.upper())
    st.divider()


def kpi_card(label: str, value: str, delta: str | None = None):
    """KPI card usando st.metric (nativo, sem HTML customizado)."""
    if delta is not None:
        clean_delta = delta.replace("▲", "").replace("▼", "").strip()
        st.metric(label=label, value=value, delta=clean_delta)
    else:
        st.metric(label=label, value=value)


def kpi_row(items: list[tuple[str, str, str | None]]):
    """Linha de KPIs usando columns nativas."""
    cols = st.columns(len(items))
    for col, (label, value, delta) in zip(cols, items):
        with col:
            kpi_card(label, value, delta)


def data_pending_notice(section: str):
    """Aviso de dados pendentes usando componente nativo."""
    st.info(f"⏳ **{section}** — integração com pipeline ETL / modelagem pendente.")
