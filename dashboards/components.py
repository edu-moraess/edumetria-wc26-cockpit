"""
dashboards/components.py
Componentes de UI reutilizáveis — KPI cards, tema Plotly, headers.
VERSÃO v5: Sem HTML customizado, 100% nativo Streamlit + Plotly.
"""
import streamlit as st
import plotly.graph_objects as go
from config import THEME, PLOTLY_BASE


def get_layout_theme() -> dict:
    return {
        "template": PLOTLY_BASE["template"],
        "paper_bgcolor": PLOTLY_BASE["paper_bgcolor"],
        "plot_bgcolor": PLOTLY_BASE["plot_bgcolor"],
        "font": PLOTLY_BASE["font"],
        "title_font": {"family": THEME["font_family"], "color": THEME["text"], "size": 13},
        "legend": {"bgcolor": "rgba(0,0,0,0)", "bordercolor": THEME["border"], "borderwidth": 1, "font": {"size": 11, "color": THEME["secondary"]}},
        "hoverlabel": {"bgcolor": THEME["surface_alt"], "bordercolor": THEME["border"], "font": {"family": THEME["font_family"], "size": 11, "color": THEME["text"]}},
        "margin": {"l": 48, "r": 24, "t": 48, "b": 40},
    }


def apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(**get_layout_theme())
    fig.update_xaxes(
        gridcolor=THEME["border"], zerolinecolor=THEME["border"],
        tickfont={"size": 10, "color": THEME["secondary"]},
        title_font={"size": 11, "color": THEME["secondary"]},
    )
    fig.update_yaxes(
        gridcolor=THEME["border"], zerolinecolor=THEME["border"],
        tickfont={"size": 10, "color": THEME["secondary"]},
        title_font={"size": 11, "color": THEME["secondary"]},
    )
    return fig


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"*{subtitle}*")
    st.markdown("---")


def kpi_card(label: str, value: str, delta: str | None = None):
    if delta:
        clean_delta = delta.replace("▲", "").replace("▼", "").strip()
        st.metric(label=label, value=value, delta=clean_delta)
    else:
        st.metric(label=label, value=value)


def kpi_row(items: list[tuple[str, str, str | None]]):
    cols = st.columns(len(items))
    for col, (label, value, delta) in zip(cols, items):
        with col:
            kpi_card(label, value, delta)


def data_pending_notice(section: str):
    st.info(f"⏳ **{section}** — integração com pipeline ETL / modelagem pendente.")
