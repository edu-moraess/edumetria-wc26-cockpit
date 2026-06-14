"""
dashboards/components.py
Componentes de UI reutilizáveis — KPI cards, page header, tema Plotly.
Paleta Quant Institutional Grade (ver config.py / THEME).
"""

import streamlit as st
import plotly.graph_objects as go

from config import THEME, PLOTLY_BASE, SERIES_PALETTE


def get_layout_theme() -> dict:
    """
    Retorna chaves de layout seguras para update_layout mesmo em subplots.
    NUNCA usar **PLOTLY_BASE diretamente em make_subplots — causa conflito de kwargs.
    """
    return {
        "template": PLOTLY_BASE["template"],
        "paper_bgcolor": PLOTLY_BASE["paper_bgcolor"],
        "plot_bgcolor": PLOTLY_BASE["plot_bgcolor"],
        "font": PLOTLY_BASE["font"],
        "title_font": {
            "family": THEME["font_family"],
            "color": THEME["text"],
            "size": 13,
        },
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": THEME["border"],
            "borderwidth": 1,
            "font": {"size": 11, "color": THEME["secondary"]},
        },
        "hoverlabel": {
            "bgcolor": THEME["surface_alt"],
            "bordercolor": THEME["border"],
            "font": {"family": THEME["font_family"], "size": 11, "color": THEME["text"]},
        },
        "margin": {"l": 48, "r": 24, "t": 48, "b": 40},
    }


def apply_theme(fig: go.Figure) -> go.Figure:
    """Aplica tema institucional Quant a uma figura Plotly (subplot-safe)."""
    fig.update_layout(**get_layout_theme())
    fig.update_xaxes(
        gridcolor=THEME["grid"],
        zerolinecolor=THEME["border"],
        tickfont={"size": 10, "color": THEME["secondary"]},
        title_font={"size": 11, "color": THEME["secondary"]},
        showspikes=True,
        spikecolor=THEME["border"],
        spikethickness=1,
    )
    fig.update_yaxes(
        gridcolor=THEME["grid"],
        zerolinecolor=THEME["border"],
        tickfont={"size": 10, "color": THEME["secondary"]},
        title_font={"size": 11, "color": THEME["secondary"]},
        showspikes=True,
        spikecolor=THEME["border"],
        spikethickness=1,
    )
    return fig


def page_header(title: str, subtitle: str = ""):
    st.markdown(
        f"<div style='font-family:{THEME[\"font_family\"]}; "
        f"font-size:1.3rem; font-weight:700; color:{THEME[\"text\"]}; "
        f"letter-spacing:0.04em; margin-bottom:0.15rem;'>{title}</div>",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f"<div style='font-family:{THEME[\"font_family\"]}; "
            f"font-size:0.78rem; color:{THEME[\"secondary\"]}; "
            f"letter-spacing:0.06em; margin-bottom:0.5rem;'>"
            f"{subtitle.upper()}</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f"<hr style='border:none; border-top:1px solid {THEME[\"border\"]}; margin:0.5rem 0 1rem 0;'/>",
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, delta: str | None = None):
    if delta is not None:
        is_negative = delta.startswith("-")
        delta_color = THEME["negative"] if is_negative else THEME["positive"]
        delta_html = (
            f"<div style='color:{delta_color}; font-size:0.75rem; "
            f"font-family:{THEME[\"font_family\"]}; margin-top:0.15rem;'>"
            f"{'▼' if is_negative else '▲'} {delta}</div>"
        )
    else:
        delta_html = ""

    st.markdown(
        f"""
        <div style="
            background-color:{THEME['surface']};
            border:1px solid {THEME['border']};
            border-left:3px solid {THEME['primary']};
            border-radius:4px;
            padding:0.75rem 1rem;
            margin-bottom:0.5rem;
        ">
            <div style="
                color:{THEME['secondary']};
                font-size:0.68rem;
                font-family:{THEME['font_family']};
                text-transform:uppercase;
                letter-spacing:0.10em;
                margin-bottom:0.25rem;
            ">{label}</div>
            <div style="
                font-size:1.45rem;
                font-weight:700;
                font-family:{THEME['font_family']};
                color:{THEME['text']};
                letter-spacing:0.02em;
            ">{value}</div>
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
        <div style="
            background-color:{THEME['surface']};
            border:1px solid {THEME['border']};
            border-left:3px solid {THEME['secondary']};
            border-radius:4px;
            padding:0.6rem 1rem;
            margin:0.5rem 0;
            font-family:{THEME['font_family']};
            font-size:0.78rem;
            color:{THEME['secondary']};
        ">
            ⏳ <strong style='color:{THEME["text"]}'>{section}</strong>
            — integração com pipeline ETL / modelagem pendente.
            Estrutura já implementada; dados reais e projeções nas próximas entregas.
        </div>
        """,
        unsafe_allow_html=True,
    )