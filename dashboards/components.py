"""
dashboards/components.py
Componentes de UI reutilizáveis — KPI cards, page header, tema Plotly.
"""

import streamlit as st
import plotly.graph_objects as go

from config import THEME, PLOTLY_BASE, SERIES_PALETTE

# Extrai variáveis para evitar escape de aspas em f-strings
bg          = THEME["background"]
surface     = THEME["surface"]
surface_alt = THEME["surface_alt"]
border      = THEME["border"]
primary     = THEME["primary"]
secondary   = THEME["secondary"]
text        = THEME["text"]
text_muted  = THEME["text_muted"]
positive    = THEME["positive"]
negative    = THEME["negative"]
warning     = THEME["warning"]
font        = THEME["font_family"]


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
    st.markdown(
        f"<div style='font-family:{font}; font-size:1.3rem; font-weight:700; "
        f"color:{text}; letter-spacing:0.04em; margin-bottom:0.15rem;'>{title}</div>",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f"<div style='font-family:{font}; font-size:0.78rem; color:{secondary}; "
            f"letter-spacing:0.06em; margin-bottom:0.5rem;'>{subtitle.upper()}</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f"<hr style='border:none; border-top:1px solid {border}; margin:0.5rem 0 1rem 0;'/>",
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, delta: str | None = None):
    if delta is not None:
        is_negative = delta.startswith("-")
        delta_color = negative if is_negative else positive
        arrow = "▼" if is_negative else "▲"
        delta_html = (
            f"<div style='color:{delta_color}; font-size:0.75rem; "
            f"font-family:{font}; margin-top:0.15rem;'>"
            f"{arrow} {delta}</div>"
        )
    else:
        delta_html = ""

    st.markdown(
        f"""
        <div style="background-color:{surface}; border:1px solid {border};
                    border-left:3px solid {primary}; border-radius:4px;
                    padding:0.75rem 1rem; margin-bottom:0.5rem;">
            <div style="color:{secondary}; font-size:0.68rem; font-family:{font};
                        text-transform:uppercase; letter-spacing:0.10em;
                        margin-bottom:0.25rem;">{label}</div>
            <div style="font-size:1.45rem; font-weight:700; font-family:{font};
                        color:{text}; letter-spacing:0.02em;">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items: list[tuple[str, str, str | None]]):
    cols = st.columns(len(items))
    for col, (label, value, delta) in zip(cols, items):
        with col:
            kpi_card(label, value, delta)


def data_pending_notice(section: str):
    st.markdown(
        f"""
        <div style="background-color:{surface}; border:1px solid {border};
                    border-left:3px solid {secondary}; border-radius:4px;
                    padding:0.6rem 1rem; margin:0.5rem 0;
                    font-family:{font}; font-size:0.78rem; color:{secondary};">
            ⏳ <strong style='color:{text}'>{section}</strong>
            — integração com pipeline ETL / modelagem pendente.
        </div>
        """,
        unsafe_allow_html=True,
    )