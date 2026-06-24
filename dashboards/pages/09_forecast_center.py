import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from dashboards.components import page_header, apply_theme
from utils.data_loader import load_indicator
from models.montecarlo.simulation_engine import run_simulation

page_header("Forecast Center", "Monte Carlo 2.0 — Projeções probabilísticas 2027–2035")

country = st.selectbox("País", ["USA", "CAN", "MEX"], index=0)
indicator = st.selectbox("Indicador", ["GDP_NOMINAL", "CPI", "UNEMPLOYMENT_RATE", "TOURISM_ARRIVALS"], index=0)

if st.button("🔮 Rodar Simulação Monte Carlo", type="primary"):
    with st.spinner("Simulando 20,000 caminhos..."):
        result = run_simulation(indicator, country, n_simulations=20000)
        if result is None:
            st.error("Dados insuficientes para simulação.")
        else:
            st.success(f"✅ Simulação concluída — Distribuição: {result['distribution']} (ν={result['df_t']:.1f})")
            years = result["forecast_years"]
            p05 = [result["percentiles"][y]["p05"] for y in years]
            p50 = [result["percentiles"][y]["p50"] for y in years]
            p95 = [result["percentiles"][y]["p95"] for y in years]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=years, y=p95, fill=None, mode="lines", line_color="rgba(0,0,0,0)", showlegend=False))
            fig.add_trace(go.Scatter(x=years, y=p05, fill="tonexty", fillcolor="rgba(76,139,245,0.15)", line_color="rgba(0,0,0,0)", name="P05–P95"))
            fig.add_trace(go.Scatter(x=years, y=p50, mode="lines+markers", name="P50 (Mediana)", line=dict(color="#4C8BF5", width=2.5)))
            fig.update_layout(title=f"Projeção {indicator} ({country}) — Monte Carlo 2.0", xaxis_title="Ano", yaxis_title="Valor")
            apply_theme(fig)
            st.plotly_chart(fig)
            
            rows = []
            for y in years:
                p = result["percentiles"][y]
                rows.append({"Ano": y, "P05": p["p05"], "P25": p["p25"], "P50": p["p50"], "P75": p["p75"], "P95": p["p95"], "Média": p["mean"]})
            st.dataframe(pd.DataFrame(rows), hide_index=True)
