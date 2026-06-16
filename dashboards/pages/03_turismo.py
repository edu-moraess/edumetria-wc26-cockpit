"""
dashboards/pages/03_turismo.py — CORRIGIDO v2
Página 3 — Turismo Internacional
Agora exibe dados REAIS do banco (StatCan/Banxico) em vez de apenas informativos.

CORREÇÕES:
- Consulta fact_indicator_values para TOURISM_ARRIVALS
- Mostra série histórica real para CAN e MEX
- Mantém baseline FIFA como referência
- Comparação CAN vs MEX com dados reais
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import FIFA_BASELINE, COUNTRY_NAMES, THEME  # noqa: E402
from dashboards.components import page_header, kpi_row, apply_theme, data_pending_notice  # noqa: E402
from database.connection import get_connection  # noqa: E402

page_header("Turismo Internacional", "Visitantes · Gastos · Permanência · Fluxos")

# ------------------------------------------------------------------
# KPIs — baseline global
# ------------------------------------------------------------------
kpi_items = [("Visitantes Totais (baseline FIFA 2026)", f"{FIFA_BASELINE['global']['visitors_total']:,}", None)]
kpi_row(kpi_items)

st.markdown("###")

# ------------------------------------------------------------------
# FUNÇÃO AUXILIAR: carregar dados de turismo
# ------------------------------------------------------------------
@st.cache_data(ttl=600)
def load_tourism_data(country_code: str) -> pd.DataFrame:
    """Carrega chegadas de turistas internacionais do banco."""
    try:
        with get_connection() as conn:
            df = conn.execute(
                """
                SELECT period, value, source_name
                FROM fact_indicator_values
                WHERE country_code = ? AND indicator_code = 'TOURISM_ARRIVALS'
                ORDER BY period
                """,
                [country_code],
            ).df()
        if not df.empty:
            df["period"] = pd.to_datetime(df["period"])
            df = df.drop_duplicates(subset=["period"], keep="last")
        return df
    except Exception as e:
        st.warning(f"Erro ao carregar dados de turismo ({country_code}): {e}")
        return pd.DataFrame()


# ------------------------------------------------------------------
# Seleção de país
# ------------------------------------------------------------------
country_code = st.selectbox(
    "País",
    ["CAN", "MEX", "USA"],
    format_func=lambda c: COUNTRY_NAMES.get(c, c),
)

tabs = st.tabs(["Série Histórica", "Setores Beneficiados (em desenvolvimento)", "Comparação CAN vs MEX"])

# ------------------------------------------------------------------
# Aba 1 — Série Histórica (AGORA COM DADOS REAIS)
# ------------------------------------------------------------------
with tabs[0]:
    st.subheader(f"Chegadas de turistas internacionais — {COUNTRY_NAMES[country_code]}")

    df = load_tourism_data(country_code)
    
    if not df.empty:
        # Gráfico
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["period"],
            y=df["value"],
            mode="lines+markers",
            name="Chegadas (mensal)",
            line=dict(color=THEME["primary"], width=2),
            marker=dict(size=4),
        ))
        fig.update_layout(
            title=f"Série histórica de chegadas internacionais — {COUNTRY_NAMES[country_code]}",
            xaxis_title="Período",
            yaxis_title="Chegadas (quantidade)",
            hovermode="x unified",
        )
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Último valor", f"{df['value'].iloc[-1]:,.0f}")
        with col2:
            st.metric("Média (últimos 12 meses)", f"{df['value'].tail(12).mean():,.0f}")
        with col3:
            st.metric("Máximo", f"{df['value'].max():,.0f}")
        with col4:
            st.metric("Mínimo", f"{df['value'].min():,.0f}")
        
        # Tabela de dados
        st.subheader("Dados detalhados")
        display_df = df.copy()
        display_df["period"] = display_df["period"].dt.strftime("%Y-%m-%d")
        display_df.columns = ["Data", "Chegadas", "Fonte"]
        st.dataframe(display_df.sort_values("Data", ascending=False), hide_index=True, use_container_width=True)
        
    else:
        if country_code == "USA":
            data_pending_notice("Turismo EUA (NTTO) — download manual pendente")
        elif country_code == "CAN":
            data_pending_notice("Turismo Canadá (StatCan) — sem dados carregados (rode o pipeline ETL)")
        elif country_code == "MEX":
            data_pending_notice("Turismo México (Banxico) — sem dados carregados (rode o pipeline ETL)")

# ------------------------------------------------------------------
# Aba 2 — Setores Beneficiados
# ------------------------------------------------------------------
with tabs[1]:
    st.subheader("Decomposição setorial do gasto turístico")
    st.markdown(
        """
        Esta seção apresentará a **receita incremental por setor**
        (hotelaria, aviação, restaurantes, varejo, entretenimento),
        decompondo o gasto turístico total observado.

        **Por que ainda não está disponível:**
        - Requer modelo de Input-Output com multiplicadores setoriais
        - Gasto médio por visitante
        - Permanência média e padrão de consumo por setor
        """
    )
    data_pending_notice("Modelo Input-Output (multiplicadores setoriais)")

# ------------------------------------------------------------------
# Aba 3 — Comparação CAN vs MEX (AGORA COM DADOS REAIS)
# ------------------------------------------------------------------
with tabs[2]:
    st.subheader("Comparação: Canadá vs. México")
    
    df_can = load_tourism_data("CAN")
    df_mex = load_tourism_data("MEX")
    
    if not df_can.empty or not df_mex.empty:
        fig = go.Figure()
        
        if not df_can.empty:
            fig.add_trace(go.Scatter(
                x=df_can["period"],
                y=df_can["value"],
                mode="lines+markers",
                name="Canadá (StatCan)",
                line=dict(color="#3FB68B", width=2),
                marker=dict(size=5),
            ))
        
        if not df_mex.empty:
            fig.add_trace(go.Scatter(
                x=df_mex["period"],
                y=df_mex["value"],
                mode="lines+markers",
                name="México (Banxico)",
                line=dict(color="#C9A227", width=2),
                marker=dict(size=5),
            ))
        
        fig.update_layout(
            title="Comparação: Chegadas internacionais — Canadá vs. México",
            xaxis_title="Período",
            yaxis_title="Chegadas (quantidade)",
            hovermode="x unified",
        )
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas comparativas
        st.subheader("Estatísticas comparativas")
        comp_data = []
        
        if not df_can.empty:
            comp_data.append({
                "País": "Canadá",
                "Última data": df_can["period"].iloc[-1].strftime("%Y-%m-%d"),
                "Último valor": f"{df_can['value'].iloc[-1]:,.0f}",
                "Média (12m)": f"{df_can['value'].tail(12).mean():,.0f}",
                "Fonte": df_can["source_name"].iloc[-1],
            })
        
        if not df_mex.empty:
            comp_data.append({
                "País": "México",
                "Última data": df_mex["period"].iloc[-1].strftime("%Y-%m-%d"),
                "Último valor": f"{df_mex['value'].iloc[-1]:,.0f}",
                "Média (12m)": f"{df_mex['value'].tail(12).mean():,.0f}",
                "Fonte": df_mex["source_name"].iloc[-1],
            })
        
        if comp_data:
            st.dataframe(pd.DataFrame(comp_data), hide_index=True, use_container_width=True)
    else:
        data_pending_notice("Comparação CAN vs MEX — sem dados carregados (rode o pipeline ETL)")
