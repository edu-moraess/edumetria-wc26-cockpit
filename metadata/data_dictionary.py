"""
metadata/data_dictionary.py
Catálogo de indicadores — Data Dictionary do Edumetria WC26 Cockpit.

Cada entrada documenta: fonte, frequência, metodologia, e status
(real / placeholder). Serve como referência única de governança de
dados e pode ser exibido em uma seção "Sobre os Dados" do dashboard.

Uso:
    from metadata.data_dictionary import DATA_DICTIONARY, print_dictionary
    python -m metadata.data_dictionary
"""

DATA_DICTIONARY = [
    {
        "indicator_code": "GDP_NOMINAL",
        "name": "PIB Nominal (EUA)",
        "source": "FRED (série GDP)",
        "frequency": "Trimestral",
        "unit": "US$ bn",
        "country": "USA",
        "methodology": "Dado oficial BEA via FRED, sem ajuste.",
        "status": "real",
    },
    {
        "indicator_code": "GDP_REAL",
        "name": "PIB Real Encadeado (EUA)",
        "source": "FRED (série GDPC1)",
        "frequency": "Trimestral",
        "unit": "Índice encadeado (2017=100)",
        "country": "USA",
        "methodology": "Dado oficial BEA via FRED, sem ajuste.",
        "status": "real",
    },
    {
        "indicator_code": "CPI",
        "name": "Índice de Preços ao Consumidor (EUA)",
        "source": "FRED (série CPIAUCSL)",
        "frequency": "Mensal",
        "unit": "Índice (1982-84=100)",
        "country": "USA",
        "methodology": "Dado oficial BLS via FRED, não dessazonalizado.",
        "status": "real",
    },
    {
        "indicator_code": "UNEMPLOYMENT_RATE",
        "name": "Taxa de Desemprego (EUA)",
        "source": "FRED (série UNRATE)",
        "frequency": "Mensal",
        "unit": "%",
        "country": "USA",
        "methodology": "Dado oficial BLS via FRED, dessazonalizado.",
        "status": "real",
    },
    {
        "indicator_code": "POLICY_RATE",
        "name": "Taxa de Política Monetária — Fed Funds (EUA)",
        "source": "FRED (série FEDFUNDS)",
        "frequency": "Mensal",
        "unit": "%",
        "country": "USA",
        "methodology": "Taxa efetiva média mensal, dado oficial Fed via FRED.",
        "status": "real",
    },
    {
        "indicator_code": "FX_INDEX",
        "name": "Índice Cambial USD (trade-weighted)",
        "source": "FRED (série DTWEXBGS)",
        "frequency": "Diária",
        "unit": "Índice (jan/2006=100)",
        "country": "USA",
        "methodology": "Broad Dollar Index, dado oficial Fed via FRED.",
        "status": "real",
    },
    {
        "indicator_code": "SP500",
        "name": "S&P 500",
        "source": "Yahoo Finance (yfinance, ticker ^GSPC)",
        "frequency": "Diária",
        "unit": "Pontos",
        "country": "USA",
        "methodology": "Preço de fechamento ajustado.",
        "status": "real",
    },
    {
        "indicator_code": "TSX",
        "name": "TSX Composite",
        "source": "Yahoo Finance (yfinance, ticker ^GSPTSE)",
        "frequency": "Diária",
        "unit": "Pontos",
        "country": "CAN",
        "methodology": "Preço de fechamento ajustado.",
        "status": "real",
    },
    {
        "indicator_code": "IPC_MEXICO",
        "name": "IPC México",
        "source": "Yahoo Finance (yfinance, ticker ^MXX)",
        "frequency": "Diária",
        "unit": "Pontos",
        "country": "MEX",
        "methodology": "Preço de fechamento ajustado.",
        "status": "real",
    },
    {
        "indicator_code": "VIX",
        "name": "VIX — Índice de Volatilidade",
        "source": "Yahoo Finance (yfinance, ticker ^VIX)",
        "frequency": "Diária",
        "unit": "Índice",
        "country": None,
        "methodology": "Volatilidade implícita 30 dias, opções S&P 500.",
        "status": "real",
    },
    {
        "indicator_code": "WTI_CRUDE",
        "name": "Petróleo WTI",
        "source": "Yahoo Finance (yfinance, ticker CL=F)",
        "frequency": "Diária",
        "unit": "US$/bbl",
        "country": None,
        "methodology": "Contrato futuro front-month, preço de fechamento.",
        "status": "real",
    },
    {
        "indicator_code": "BRENT_CRUDE",
        "name": "Petróleo Brent",
        "source": "Yahoo Finance (yfinance, ticker BZ=F)",
        "frequency": "Diária",
        "unit": "US$/bbl",
        "country": None,
        "methodology": "Contrato futuro front-month, preço de fechamento.",
        "status": "real",
    },
    {
        "indicator_code": "ETF_AVIATION",
        "name": "ETF Setor Aviação (JETS)",
        "source": "Yahoo Finance (yfinance, ticker JETS)",
        "frequency": "Diária",
        "unit": "US$",
        "country": None,
        "methodology": "Preço de fechamento ajustado. Proxy setorial, não índice oficial.",
        "status": "real",
    },
    {
        "indicator_code": "ETF_LEISURE",
        "name": "ETF Lazer/Entretenimento (PEJ)",
        "source": "Yahoo Finance (yfinance, ticker PEJ)",
        "frequency": "Diária",
        "unit": "US$",
        "country": None,
        "methodology": "Preço de fechamento ajustado. Proxy setorial, não índice oficial.",
        "status": "real",
    },
    {
        "indicator_code": "ETF_CONSUMER_DISCRETIONARY",
        "name": "ETF Consumo Discricionário (XLY)",
        "source": "Yahoo Finance (yfinance, ticker XLY)",
        "frequency": "Diária",
        "unit": "US$",
        "country": "USA",
        "methodology": "Preço de fechamento ajustado. Proxy setorial, não índice oficial.",
        "status": "real",
    },
    {
        "indicator_code": "TOURISM_ARRIVALS",
        "name": "Chegadas de Turistas Internacionais",
        "source": "StatCan (Canadá) / Banxico SIE (México)",
        "frequency": "Mensal",
        "unit": "Contagem",
        "country": "CAN, MEX",
        "methodology": "Dado oficial dos institutos estatísticos nacionais. "
                        "EUA (NTTO) pendente de integração manual.",
        "status": "real",
    },
    # ------------------------------------------------------------------
    # INDICADORES PLANEJADOS (ainda não implementados)
    # ------------------------------------------------------------------
    {
        "indicator_code": "GDP_INCREMENTAL_NET",
        "name": "PIB Incremental Líquido (Copa 2026)",
        "source": "Modelo interno (Input-Output + contrafactual)",
        "frequency": "Anual",
        "unit": "US$ bn",
        "country": "USA, CAN, MEX",
        "methodology": "Pendente — requer models/econometric/net_impact.py "
                        "(impacto bruto - contrafactual via Synthetic Control/DiD).",
        "status": "planejado",
    },
    {
        "indicator_code": "WCLI",
        "name": "World Cup Legacy Index",
        "source": "Modelo interno (composto ponderado)",
        "frequency": "Anual",
        "unit": "0-100",
        "country": "USA, CAN, MEX",
        "methodology": "Componente Turismo implementado (models/montecarlo/"
                        "wcli_calculator.py); demais componentes (PIB, "
                        "Emprego, FDI, Infraestrutura, ESG) pendentes.",
        "status": "parcial",
    },
    {
        "indicator_code": "WORLD_CUP_RISK_SCORE",
        "name": "World Cup Risk Score",
        "source": "Modelo interno (composto: VIX, petróleo, FX)",
        "frequency": "Diária",
        "unit": "0-100",
        "country": None,
        "methodology": "models/montecarlo/risk_score.py — percentil "
                        "histórico de VIX, desvio do WTI vs. média 252d, "
                        "e volatilidade realizada do FX_INDEX.",
        "status": "real",
    },
]


def print_dictionary():
    print(f"{'Código':28s} {'Nome':40s} {'Status':12s} {'Fonte'}")
    print("-" * 110)
    for entry in DATA_DICTIONARY:
        print(f"{entry['indicator_code']:28s} {entry['name']:40s} {entry['status']:12s} {entry['source']}")


if __name__ == "__main__":
    print_dictionary()
