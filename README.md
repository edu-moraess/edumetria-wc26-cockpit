# Edumetria WC26 Cockpit
### FIFA World Cup 2026™ — Impact Analytics Platform

**Eduardo Moraes · Quant Data Scientist & Economics Researcher · Edumetria**

[

![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)

](https://edumetriaquant.streamlit.app)

Plataforma analítica institucional para monitoramento, análise e projeção
dos impactos macroeconômicos, financeiros, geopolíticos e sociais da
Copa do Mundo FIFA 2026™ (EUA · Canadá · México), horizonte 2026–2035.

Qualidade equivalente a projetos de pesquisa de IMF, World Bank, Goldman
Sachs Research e bancos centrais — com transparência total de metodologia,
limitações e premissas.

---

## Dashboard ao vivo

**[edumetriaquant.streamlit.app](https://edumetriaquant.streamlit.app)**

---

## Páginas

| # | Página | Dados reais | Status |
|---|--------|------------|--------|
| 1 | Executive Overview | Turismo (CAN/MEX), snapshot de mercado | ✅ |
| 2 | Macroeconomia | FRED (PIB, CPI, juros, desemprego, yield spread) | ✅ |
| 3 | Turismo | StatCan (Canadá) · Banxico (México) | ✅ |
| 4 | Aviação | WTI como proxy de custo de combustível | ✅ parcial |
| 5 | Hotelaria | — (STR Global, fonte paga) | ⏳ |
| 6 | Mercado Financeiro | yfinance (índices, ETFs, drawdown, correlação, vol.) | ✅ |
| 7 | Geopolítica | WTI, Brent, VIX, World Cup Risk Score | ✅ |
| 8 | ESG | — (dados de emissões pendentes) | ⏳ |
| 9 | Forecast Center | Monte Carlo 20k simulações (bootstrap paramétrico) | ✅ |

---

## Fontes de dados

| Fonte | Cobertura | Custo |
|-------|-----------|-------|
| FRED (Federal Reserve) | Macro EUA: PIB, CPI, juros, câmbio, Treasuries | Grátis |
| Yahoo Finance (yfinance) | Índices, ETFs, WTI, Brent, VIX | Grátis |
| Statistics Canada (StatCan) | Turismo e macro Canadá | Grátis |
| Banxico SIE | Turismo México | Grátis (token) |
| INEGI | Macro México | Grátis (token) |
| STR Global / OAG / IATA | Hotelaria e aviação | Pago — fase pós-MVP |

---

## Modelos implementados

- **World Cup Risk Score (0–100)** — percentil histórico de VIX,
  choque no petróleo (WTI vs. média 252d) e volatilidade cambial (FX Index)
- **World Cup Legacy Index (WCLI)** — índice composto ponderado
  (componente turismo ativo; PIB/Emprego/FDI/Infra/ESG pendentes)
- **Monte Carlo (20.000 simulações)** — bootstrap paramétrico com
  distribuições históricas (PIB, CPI, desemprego EUA; turismo CAN/MEX)
- **Yield Spread 10Y–2Y** — indicador derivado (FRED), integrado
  à análise de risco de recessão pré-Copa

---

## Arquitetura

edumetria-wc26-cockpit/
├── config.py               # configuração central (tema quant, baseline FIFA, WCLI)
├── config_secrets.py       # helper st.secrets ↔ os.getenv
├── requirements.txt
│
├── data/
│   ├── raw/                # snapshots imutáveis das fontes
│   ├── processed/          # dados normalizados (parquet)
│   └── external/           # datasets de terceiros
│
├── database/
│   ├── schema.sql          # star schema (dim_* + fact_*)
│   └── connection.py       # DuckDB (dev) / Postgres (produção)
│
├── etl/
│   ├── extractors/         # 1 módulo por fonte (fred, yfinance, statcan, banxico, inegi)
│   ├── transformers/       # limpeza, normalização, indicadores derivados
│   ├── loaders/            # carga no DW (truncate + reload — sem duplicação)
│   └── run_pipeline.py     # orquestrador (chamado pelo botão do dashboard)
│
├── models/
│   ├── econometric/        # I-O, contrafactual, GARCH-X, Ridge-VAR (fase pós-MVP)
│   ├── ml/                 # XGBoost, LightGBM, Prophet, LSTM (fase pós-MVP)
│   └── montecarlo/         # Risk Score, WCLI, simulação, FIFA Auditor
│
├── metadata/
│   └── data_dictionary.py  # catálogo completo de indicadores
│
├── dashboards/
│   ├── app.py              # entry point Streamlit (tema quant, navegação, ETL)
│   ├── components.py       # KPI cards, apply_theme() subplot-safe
│   └── pages/              # 9 páginas (01_executive_overview → 09_forecast_center)
│
├── deployment/
│   ├── docker/             # Dockerfile + docker-compose
│   └── streamlit_cloud/    # config.toml + guia de deploy
│
└── tests/                  # pytest (em desenvolvimento)


---

## Como executar localmente

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas chaves de API

# 3. Inicializar schema do banco
python database/connection.py

# 4. Rodar o pipeline ETL (baixa dados das APIs)
python -m etl.run_pipeline

# 5. Iniciar o dashboard
streamlit run dashboards/app.py

Deploy (Streamlit Cloud)
Fork ou clone este repositório
Em share.streamlit.io, aponte para dashboards/app.py
Em Settings → Secrets, adicione:

FIFA2026_DB_BACKEND = "duckdb"
FRED_API_KEY        = "sua_chave_fred"
BANXICO_TOKEN       = "seu_token_banxico"
INEGI_TOKEN         = "seu_token_inegi"

Clique "↺ Atualizar dados" na sidebar do app para popular o banco
Nota: o DuckDB no Streamlit Cloud é efêmero — os dados são
recarregados a cada restart do app. Para persistência entre sessões,
migrar para Postgres gerenciado (Supabase / Neon free tier).
