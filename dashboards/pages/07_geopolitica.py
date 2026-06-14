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