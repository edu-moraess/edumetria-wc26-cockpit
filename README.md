Edumetria WC26 Cockpit

FIFA World Cup 2026™ Economic, Financial & Geopolitical Analytics Platform

Eduardo Moraes
Quantitative Data Scientist · Economics Researcher · Systems & Control Engineering Student

""Streamlit App" (https://static.streamlit.io/badges/streamlit_badge_black_white.svg)" (https://edumetriaquant.streamlit.app)

---

Executive Summary

The Edumetria WC26 Cockpit is a quantitative analytics platform designed to monitor, analyze and project the potential economic, financial, geopolitical and sectoral impacts associated with the FIFA World Cup 2026™, hosted by the United States, Canada and Mexico.

The platform integrates public datasets from central banks, national statistical agencies and global financial markets to build proprietary indicators, risk monitoring frameworks and forward-looking economic scenarios.

The project combines:

- Data Engineering
- Quantitative Analytics
- Applied Economics
- Risk Modeling
- Forecasting
- Data Visualization

within a fully reproducible analytical environment.

Analysis Horizon: 2026–2035

---

Research Motivation

Mega sporting events are often associated with expectations regarding:

- Economic growth
- Tourism expansion
- Infrastructure development
- Labor market effects
- Foreign investment attraction
- Long-term economic legacy

However, empirical evidence frequently shows mixed results.

The purpose of this project is to provide a transparent and reproducible framework for analyzing these potential impacts using real-world data, quantitative methods and clearly documented assumptions.

---

Live Dashboard

Production Environment

https://edumetriaquant.streamlit.app

---

Analytical Framework

The platform is organized into four analytical pillars.

Economic Monitoring

Monitoring macroeconomic conditions across host countries.

Financial Markets Monitoring

Tracking market performance, volatility and investor sentiment.

Geopolitical & Risk Monitoring

Assessing global uncertainty and macro-financial stress conditions.

Forecasting & Scenario Analysis

Building probabilistic projections and forward-looking scenarios.

---

Dashboard Modules

Module| Description| Status
Executive Overview| Executive summary of key indicators| ✅
Macroeconomics| GDP, CPI, interest rates, unemployment and yield curve| ✅
Tourism Analytics| Tourism flows and sector monitoring| ✅
Aviation Monitor| Energy and aviation-related indicators| ✅ Partial
Hospitality Analytics| Hotel occupancy and accommodation indicators| 🚧
Financial Markets| Indices, ETFs, volatility, drawdowns and correlations| ✅
Geopolitical Monitor| Global risk and uncertainty indicators| ✅
ESG Dashboard| Sustainability and environmental indicators| 🚧
Forecast Center| Monte Carlo simulations and scenario analysis| ✅

---

Data Sources

Macroeconomic Data

- Federal Reserve Economic Data (FRED)
- Statistics Canada (StatCan)
- Banco de México (Banxico)
- Instituto Nacional de Estadística y Geografía (INEGI)

Financial Markets

- Yahoo Finance
- Treasury Market Data

Energy Markets

- West Texas Intermediate (WTI)
- Brent Crude Oil

Future Integrations

- International Monetary Fund (IMF)
- World Bank
- OECD
- IATA
- OAG
- STR Global

---

Quantitative Models

World Cup Risk Score (WCRS)

Proprietary framework designed to monitor global macro-financial stress through:

- Volatility indicators
- Energy market conditions
- Financial market dynamics

---

World Cup Legacy Index (WCLI)

Experimental composite framework designed to assess potential long-term economic legacy effects associated with the tournament.

Current implementation focuses primarily on tourism metrics, with future expansion planned for:

- GDP
- Employment
- Foreign Direct Investment (FDI)
- Infrastructure
- ESG metrics

---

Monte Carlo Forecast Engine

The Forecast Center currently implements:

- Parametric Bootstrap
- Monte Carlo Simulation
- Historical Volatility Modeling

Current configuration:

- 20,000 simulations
- Percentile analysis
- Scenario distributions
- Probabilistic forecasting

---

Yield Curve Monitor

Monitoring of Treasury yield spreads as an early-warning macroeconomic indicator.

Current implementation:

- 10Y–2Y Spread
- Recession Risk Assessment

---

Forecast Center Methodology

The current forecasting framework is designed as a transparent MVP architecture.

Implemented

- Historical growth distributions
- Parametric bootstrap simulations
- Confidence interval generation
- Percentile forecasting

Current Limitations

- Assumes normality of increments
- Does not model regime changes
- Does not include extreme-tail events
- Does not incorporate exogenous World Cup shocks
- Does not model cross-country dependencies

All limitations are explicitly documented to ensure methodological transparency.

---

Technical Architecture

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

---

Data Pipeline

External APIs
      │
      ▼
   Extract
      │
      ▼
  Transform
      │
      ▼
     Load
      │
      ▼
Data Warehouse
      │
      ▼
Quant Models
      │
      ▼
 Dashboard

---

Research Roadmap

Econometrics & Causal Inference

Planned future implementations:

- Difference-in-Differences (DiD)
- Synthetic Control
- Event Studies
- Ridge VAR
- GARCH-X
- Local Projections
- Input-Output Models

---

Machine Learning

Planned future implementations:

- XGBoost
- LightGBM
- Prophet
- LSTM

---

Risk Analytics

Planned future implementations:

- Extreme Value Theory (EVT)
- Stress Testing
- Regime Switching Models
- Scenario Analysis
- Sovereign Risk Monitoring

---

Legacy Impact Assessment

Future research modules:

- Historical World Cup Benchmarking
- Counterfactual Analysis
- Infrastructure Impact Assessment
- Tourism Legacy Analysis
- Foreign Investment Impact Analysis

---

Methodological Principles

The project follows the following principles:

- Transparency
- Reproducibility
- Auditability
- Explicit Assumptions
- Documented Limitations

Results should not be interpreted as investment advice, official forecasts or policy recommendations.

---

Project Status

Current Stage

MVP Completed

✅ Data Ingestion

✅ ETL Pipeline

✅ Data Warehouse

✅ Quantitative Dashboard

✅ Forecast Center

✅ Proprietary Indicators

✅ Risk Monitoring Framework

---

Under Development

🚧 Econometric Models

🚧 Causal Inference Frameworks

🚧 Counterfactual Analysis

🚧 Legacy Impact Estimation

🚧 Advanced Risk Analytics

---

Future Vision

The long-term objective is to evolve the platform into a research-grade analytical environment for:

- Economic Impact Assessment
- Risk Analytics
- Applied Econometrics
- Policy Evaluation
- Mega-Event Economics

inspired by analytical frameworks commonly used by central banks, multilateral organizations and economic research institutions.

---

Author

Eduardo Moraes

Quantitative Data Scientist

Economics Researcher

Systems & Control Engineering Student

Independent Research Project

---

Disclaimer

FIFA World Cup 2026™ is a trademark of FIFA.

This project is an independent academic and analytical initiative and is not affiliated with, endorsed by or sponsored by FIFA.