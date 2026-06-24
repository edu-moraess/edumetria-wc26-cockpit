# ⚽ FIFA World Cup 2026™ — Impact Analytics Platform

**Plataforma quantitativa institucional para monitoramento, análise e projeção dos impactos da Copa do Mundo FIFA 2026™.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://quantasystemdev.streamlit.app)

> **Autor:** Eduardo Moraes · Quant Data Scientist & Economics Researcher · Edumetria

---

## O que é

O WC26 Cockpit é um **sistema de inteligência quantitativa** para o maior evento esportivo da história. Ele não apenas descreve o impacto da Copa — ele **mede, projeta e contrafactualiza** o impacto em tempo real.

**Proposição de valor:**
> "Dados, não hype. Métricas, não promessas."

---

## Dashboard ao vivo

**URL:** [quantasystemdev.streamlit.app](https://quantasystemdev.streamlit.app)

### 10 Páginas — Todas com dados reais

| # | Página | Dados | Status |
|---|--------|-------|--------|
| 1 | **Executive Overview** | S&P 500, VIX, WTI, TSX, WCLI, Turismo CAN/MEX | ✅ |
| 2 | **Macroeconomia** | PIB, CPI, Juros, Desemprego, Yield Spreads (EUA/CAN/MEX) | ✅ |
| 3 | **Turismo** | Chegadas internacionais CAN/MEX (StatCan/Banxico) | ✅ |
| 4 | **Aviação** | Tráfego aéreo (TSA proxy), Jet Fuel, Ações (LUV, DAL, UAL, AAL), JETS ETF | ✅ |
| 5 | **Hotelaria** | ADR, Ocupação, RevPAR, Ações (MAR, HLT, H) | ✅ |
| 6 | **Mercado Financeiro** | S&P 500, Nasdaq, TSX, IPC, Commodities, VIX | ✅ |
| 7 | **Geopolítica** | Risk Score 2.0 (4 dimensões), Commodities, VIX | ✅ |
| 8 | **ESG** | CO₂, Energia Renovável, Consumo de Energia (EUA/CAN/MEX) | ✅ |
| 9 | **Forecast Center** | Monte Carlo 2.0 — Student-t, 20k simulações, P05-P95 | ✅ |
| 10 | **Recession Monitor** | Sahm Rule, Yield Spreads, Leading Index, Fed NY | ✅ |

---

## Arquitetura

edumetria-wc26-cockpit/ ├── config.py # Configuração central ├── config_secrets.py # Secrets helper ├── utils/ │ ├── data_loader.py # Loader cacheado (st.cache_data) │ └── page_template.py # Template padrão para páginas ├── database/ │ ├── schema.sql # Star schema │ └── connection.py # DuckDB / Postgres ├── etl/ │ ├── extractors/ # 8 fontes de dados │ ├── transformers/ # 6 normalizadores │ └── loaders/ │ └── load_indicators.py # Loader com catálogo completo ├── models/ │ ├── econometric/ # DiD, Synthetic Control │ └── montecarlo/ # Monte Carlo, WCLI, Risk Score, Recession Monitor ├── dashboards/ │ ├── app.py # Entry point │ ├── components.py # UI reutilizável │ └── pages/ # 10 abas ├── api/ │ └── main.py # FastAPI (12 endpoints) └── tests/ # pytest


---

## Modelos Quantitativos

| Modelo | Metodologia | Referência |
|--------|-------------|------------|
| **Monte Carlo 2.0** | Student-t MLE (fat tails), 20k simulações | McNeil, Frey & Embrechts (2015) |
| **DiD** | Difference-in-Differences com controles | Angrist & Pischke (2009) |
| **Synthetic Control** | Abadie-Diamond-Hainmueller (2010) | Abadie et al. (2010) |
| **WCLI v4** | Índice composto 6 dimensões, completeness-aware | Proprietário |
| **Risk Score 2.0** | 4 camadas (financeira, energética, macro, geopolítica) | Caldara & Iacoviello (2022) |
| **Recession Monitor** | 5 componentes compostos | Sahm (2019), Estrella & Mishkin (1998) |

---

## Fontes de Dados

| Fonte | Dados | Token |
|-------|-------|-------|
| **FRED** | Macro EUA, Treasuries, Sahm Rule, Leading Index | Grátis |
| **yfinance** | Índices, ETFs, Commodities, Ações | Não |
| **StatCan** | Turismo CAN, Macro CAN | Não |
| **Banxico** | Turismo MEX | Grátis |
| **Bank of Canada** | Taxa overnight, CPI, Câmbio | Não |
| **World Bank** | Histórico Copas, FDI, CO₂ | Não |

---

## Instalação

```bash
# 1. Clone
git clone https://github.com/edu-moraess/edumetria-wc26-cockpit.git
cd edumetria-wc26-cockpit

# 2. Instale dependências
pip install -r requirements.txt

# 3. Configure secrets
cp .env.example .env
# Edite .env: FRED_API_KEY, BANXICO_TOKEN

# 4. Inicialize o banco
python database/connection.py

# 5. Rode o ETL
python -m etl.run_pipeline

# 6. Inicie o dashboard
streamlit run dashboards/app.py

Deploy Streamlit Cloud
1. 
Fork no GitHub
2. 
Aponte  dashboards/app.py  como main file
3. 
Copie  .streamlit/config.toml  para a raiz
4. 
Configure Secrets (FRED_API_KEY, BANXICO_TOKEN)
5. 
Clique "Atualizar dados" na sidebar
Licença
MIT License — Eduardo Moraes · Edumetria · 2026