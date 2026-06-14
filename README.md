Edumetria WC26 Cockpit

FIFA World Cup 2026™ — Impact Analytics Platform

Eduardo MoraesQuantitative Data Scientist · Economics Researcher · Edumetria



Plataforma analítica para monitoramento, análise e projeção dos impactos econômicos, financeiros, geopolíticos e setoriais associados à Copa do Mundo FIFA 2026™, sediada por Estados Unidos, Canadá e México.

O projeto integra dados públicos de instituições governamentais, bancos centrais e mercados financeiros para construção de indicadores proprietários, cenários prospectivos e modelos quantitativos voltados à avaliação de riscos, oportunidades e efeitos de legado do evento.

Horizonte Analítico: 2026–2035

Dashboard

Acesse:

https://edumetriaquant.streamlit.app

Objetivos

Monitorar indicadores macroeconômicos dos países-sede

Avaliar impactos potenciais sobre turismo, mercado financeiro e infraestrutura

Construir métricas quantitativas de risco e legado econômico

Disponibilizar análises transparentes, reproduzíveis e auditáveis

Desenvolver um laboratório aplicado de Data Science, Economia e Sistemas Quantitativos

Módulos do Dashboard

Página

Descrição

Status

Executive Overview

Visão executiva dos principais indicadores

✅

Macroeconomia

PIB, inflação, juros, desemprego e curva de juros

✅

Turismo

Fluxo turístico e indicadores setoriais

✅

Aviação

Custos energéticos e proxies operacionais

✅ Parcial

Hotelaria

Indicadores de ocupação e receita

🚧 Em desenvolvimento

Mercado Financeiro

Índices, ETFs, volatilidade e correlações

✅

Geopolítica

Indicadores de risco global e energia

✅

ESG

Indicadores ambientais e sustentabilidade

🚧 Em desenvolvimento

Forecast Center

Simulações e cenários prospectivos

✅

Fontes de Dados

Fonte

Aplicação

FRED (Federal Reserve Economic Data)

Indicadores macroeconômicos dos EUA

Yahoo Finance (yfinance)

Mercados financeiros e commodities

Statistics Canada (StatCan)

Dados econômicos e turísticos do Canadá

Banxico SIE

Indicadores econômicos e turismo do México

INEGI

Estatísticas econômicas mexicanas

World Bank (Roadmap)

Indicadores estruturais e comparativos

IMF Data (Roadmap)

Séries macroeconômicas globais

STR Global (Planejado)

Hotelaria

IATA / OAG (Planejado)

Aviação

Indicadores Proprietários

World Cup Risk Score (WCRS)

Índice sintético de risco baseado em:

Volatilidade implícita (VIX)

Choques nos preços do petróleo

Volatilidade cambial

Normalização por percentis históricos

Escala:

0–33 → Baixo risco

34–66 → Risco moderado

67–100 → Alto risco

World Cup Legacy Index (WCLI)

Índice de legado econômico estruturado para incorporar:

Turismo

Crescimento econômico

Emprego

Investimento estrangeiro direto (FDI)

Infraestrutura

Sustentabilidade (ESG)

Atualmente em fase de expansão metodológica.

Modelagem Quantitativa

Implementado

Monte Carlo Simulation (20.000 cenários)

Bootstrap Paramétrico

Yield Spread Analysis (10Y–2Y)

Risk Scoring Framework

Drawdown Analysis

Volatility Monitoring

Correlation Analysis

Roadmap

VAR / Ridge-VAR

GARCH-X

Difference-in-Differences

Synthetic Control

Input-Output Models

XGBoost

LightGBM

Prophet

LSTM

Arquitetura

edumetria-wc26-cockpit/
│
├── config.py
├── requirements.txt
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── database/
│   ├── schema.sql
│   └── connection.py
│
├── etl/
│   ├── extractors/
│   ├── transformers/
│   ├── loaders/
│   └── run_pipeline.py
│
├── models/
│   ├── econometric/
│   ├── ml/
│   └── montecarlo/
│
├── metadata/
│   └── data_dictionary.py
│
├── dashboards/
│   ├── app.py
│   ├── components.py
│   └── pages/
│
├── deployment/
│   ├── docker/
│   └── streamlit_cloud/
│
└── tests/

Execução Local

pip install -r requirements.txt

cp .env.example .env

python database/connection.py

python -m etl.run_pipeline

streamlit run dashboards/app.py

Deploy

Streamlit Cloud

Configurar os seguintes Secrets:

FIFA2026_DB_BACKEND = "duckdb"

FRED_API_KEY = "your_key"

BANXICO_TOKEN = "your_token"

INEGI_TOKEN = "your_token"

Após o deploy, utilize a opção Atualizar Dados para executar o pipeline ETL diretamente pela interface.

Limitações

Parte dos indicadores setoriais ainda depende de bases pagas.

O projeto não constitui recomendação de investimento.

Resultados de simulações dependem das premissas adotadas.

Algumas métricas encontram-se em fase experimental.

Licença

MIT License

Autor

Eduardo Moraes

Quantitative Data Scientist · Economics Researcher

Projeto independente de pesquisa aplicada em Economia, Data Science e Sistemas Quantitativos voltados à Copa do Mundo FIFA 2026™.