# Edumetria WC26 Cockpit
### FIFA World Cup 2026™ — Impact Analytics Platform

**Eduardo Moraes · Quant Data Scientist & Economics Researcher · Edumetria**

[

![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)

](https://edumetriaquant.streamlit.app)

Plataforma analítica institucional para monitoramento, análise e projeção
dos impactos macroeconômicos, financeiros, geopolíticos e sociais da
Copa do Mundo FIFA 2026™ (EUA · Canadá · México), horizonte 2026–2035.

---

## Dashboard ao vivo

**[edumetriaquant.streamlit.app](https://edumetriaquant.streamlit.app)**

---

## Páginas

| # | Página | Dados reais | Status |
|---|--------|------------|--------|
| 1 | Executive Overview | Turismo CAN/MEX · Snapshot de mercado · WCLI parcial | ✅ |
| 2 | Macroeconomia | FRED: PIB, CPI, Juros, Desemprego, Yield Spread EUA | ✅ |
| 3 | Turismo | StatCan (Canadá) · Banxico (México) | ✅ |
| 4 | Aviação | WTI como proxy custo jet fuel | ✅ parcial |
| 5 | Hotelaria | STR Global (pago) — placeholder documentado | ⏳ |
| 6 | Mercado Financeiro | yfinance: índices, ETFs, drawdown, correlação, vol. | ✅ |
| 7 | Geopolítica | Risk Score 2.0 · WTI/Brent/NG (eixos separados) · VIX · HY Spread | ✅ |
| 8 | ESG | Placeholder documentado (emissões dependem de dados de aviação) | ⏳ |
| 9 | Forecast Center | Monte Carlo 2.0 (Student-t, 20k simulações) | ✅ |
| 10 | Recession Monitor | Sahm Rule · Yield Spreads · Leading Index · Fed NY | ✅ |

---

## Fontes de dados

### Ativas (funcionando hoje)

| Fonte | Cobertura | Token necessário |
|-------|-----------|-----------------|
| **FRED** (Federal Reserve) | Macro EUA: PIB, CPI, juros, desemprego, Treasuries, Sahm Rule, Leading Index, HY Spread, MOVE Index, SOFR | **Sim** (grátis, instantâneo) |
| **Yahoo Finance** (yfinance) | Índices (S&P500, TSX, IPC), ETFs, WTI, Brent, VIX, Gás Natural, Ouro, Nasdaq | Não |
| **Statistics Canada** (StatCan) | Chegadas turísticas internacionais ao Canadá | Não |
| **Banxico SIE** | Chegadas turísticas ao México | **Sim** (grátis, instantâneo) |
| **Bank of Canada** (Valet API) | Taxa overnight, CPI, câmbio CAD/USD, desemprego Canadá | Não |

### Prontas para ativar (sem token adicional)

| Fonte | Cobertura | Status |
|-------|-----------|--------|
| **World Bank API** | Macro histórico 2000-2024 · Turismo Copa anteriores · Países controle DiD | Extractor pronto — integrar ao pipeline |
| **INEGI** | Macro México: PIB, CPI, desemprego | Extractor pronto — requer token INEGI |

### Futuras (pós-MVP)

| Fonte | Cobertura | Observação |
|-------|-----------|------------|
| **GPR Index** (Caldara & Iacoviello) | Risco geopolítico global — componente Geopolítico do Risk Score 2.0 | Download manual em matteoiacoviello.com/gpr.htm |
| **US NTTO** | Turismo EUA | Download manual em trade.gov/national-travel-tourism-office |
| **STR Global** | Hotelaria: ADR, RevPAR, Ocupação | Pago (B2B) |
| **OAG / IATA** | Aviação: rotas, assentos, passageiros | Pago (B2B) |
| **IMF Data API** | Macro multilateral | Sem token, endpoints em validação |
| **OECD API** | Macro países OCDE | Sem token, endpoints em validação |

---

## Modelos implementados

### Risk Score 2.0 (0–100)
Framework multicamadas com 4 dimensões:
- **Financeira (35%)**: VIX, MOVE Index, HY Spread, SOFR
- **Energética (25%)**: WTI, Brent, Gás Natural (desvio vs. média 252d)
- **Macroeconômica (25%)**: Yield Spread 10Y-2Y, 10Y-3M, Leading Index
- **Geopolítica (15%)**: GPR Index — pendente de integração manual

### Recession Monitor
Score composto de probabilidade de recessão (0–100):
- Yield Spread 10Y-2Y (proxy sigmóide do modelo probit Fed NY)
- Yield Spread 10Y-3M (modelo Estrella & Mishkin, 1998)
- Sahm Rule (Sahm, 2019) — threshold: 0.5pp
- Leading Economic Index (Conference Board)
- Probabilidade oficial Fed NY (modelo probit)

### World Cup Legacy Index (WCLI)
Índice composto ponderado (0–100):
- PIB (25%), Emprego (20%), Turismo (20%), FDI (15%), Infraestrutura (10%), ESG (10%)
- Componente Turismo implementado com dados reais
- Demais componentes dependem de modelagem econométrica (fase pós-MVP)

### Monte Carlo 2.0 (20.000 simulações)
- Distribuição **Student-t** (fat tails) — ajuste por MLE
- Fallback automático para Normal se MLE falhar
- Horizonte 2027–2035
- Percentis P05, P25, P50, P75, P95

---

## Arquitetura

edumetria-wc26-cockpit/
│
├── config.py               # tema quant, baseline FIFA, WCLI, paleta
├── config_secrets.py       # st.secrets ↔ os.getenv (local + Streamlit Cloud)
├── requirements.txt
│
├── data/
│   ├── raw/                # snapshots imutáveis (CSV por data, nunca editados)
│   ├── processed/          # parquets normalizados prontos para o banco
│   └── external/           # datasets manuais (GPR, NTTO, etc.)
│       ├── ntto_usa/       # turismo EUA — download manual
│       └── gpr/            # GPR Index — download manual
│
├── database/
│   ├── schema.sql          # star schema (dim_* + fact_*)
│   └── connection.py       # DuckDB (dev) / Postgres (prod)
│
├── etl/
│   ├── extractors/
│   │   ├── fred.py                  # macro EUA (PIB, CPI, juros, Treasuries)
│   │   ├── fred_expanded.py         # SOFR, MOVE, Sahm Rule, Leading Index, HY Spread
│   │   ├── yfinance_markets.py      # índices, ETFs, WTI, Brent, VIX
│   │   ├── yfinance_expanded.py     # Natural Gas, Gold, Nasdaq, Russell
│   │   ├── tourism_open_sources.py  # StatCan (turismo CAN) + Banxico (turismo MEX)
│   │   ├── statcan_macro.py         # macro Canadá via StatCan
│   │   ├── bank_of_canada.py        # BoC Valet API (sem token)
│   │   ├── inegi.py                 # macro México (requer INEGI_TOKEN)
│   │   └── world_bank.py            # histórico Copa anteriores + países controle DiD
│   │
│   ├── transformers/
│   │   ├── clean_macro.py           # FRED → tidy + Yield Spread 10Y-2Y derivado
│   │   ├── clean_markets.py         # yfinance → tidy
│   │   ├── clean_tourism.py         # StatCan + Banxico → tidy
│   │   ├── clean_macro_can_mex.py   # StatCan macro + INEGI → tidy
│   │   ├── clean_bank_of_canada.py  # BoC → tidy
│   │   └── clean_expanded.py        # FRED expanded + yfinance expanded → tidy
│   │                                  + Yield Spread 10Y-3M derivado
│   ├── loaders/
│   │   └── load_indicators.py       # truncate + reload em fact_indicator_values
│   │
│   └── run_pipeline.py              # orquestrador com retry (2 tentativas + backoff 5s)
│
├── models/
│   ├── econometric/                 # DiD, Synthetic Control (fase pós-MVP)
│   ├── ml/                          # XGBoost, LightGBM, Prophet, LSTM (fase pós-MVP)
│   └── montecarlo/
│       ├── simulation_engine.py     # Monte Carlo 2.0 (Student-t)
│       ├── wcli_calculator.py       # WCLI por país/cenário
│       ├── risk_score_v2.py         # World Cup Risk Score 2.0 (4 dimensões)
│       ├── recession_monitor.py     # Recession Monitor (5 indicadores)
│       └── fifa_auditor.py          # auditoria estrutural das projeções FIFA
│
├── metadata/
│   └── data_dictionary.py           # catálogo completo de indicadores
│
├── dashboards/
│   ├── app.py                       # entry point (tema quant, ETL, navegação)
│   ├── components.py                # KPI cards, apply_theme() subplot-safe
│   └── pages/
│       ├── 01_executive_overview.py
│       ├── 02_macroeconomia.py      # FRED: PIB, CPI, Juros, Yield Spread
│       ├── 03_turismo.py            # StatCan + Banxico
│       ├── 04_aviacao.py            # WTI como proxy
│       ├── 05_hotelaria.py          # placeholder documentado
│       ├── 06_mercado_financeiro.py # yfinance: drawdown, correlação, vol.
│       ├── 07_geopolitica.py        # Risk Score 2.0 + energia (eixo duplo)
│       ├── 08_esg.py                # placeholder documentado
│       ├── 09_forecast_center.py    # Monte Carlo 2.0
│       └── 10_recession_monitor.py  # Sahm + Spreads + Leading + Fed NY
│
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── streamlit_cloud/
│       ├── config.toml              # tema dark (copiar para .streamlit/config.toml)
│       ├── DEPLOY.md                # guia de deploy
│       └── SECRETS_TEMPLATE.toml   # template de Secrets para Streamlit Cloud
│
└── tests/                           # pytest (em desenvolvimento)

---

## Como executar localmente

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env: preencher FRED_API_KEY (obrigatório) e BANXICO_TOKEN (recomendado)

# 3. Inicializar schema do banco
python database/connection.py

# 4. Rodar pipeline ETL (baixa dados de todas as APIs configuradas)
python -m etl.run_pipeline

# 5. Iniciar o dashboard
streamlit run dashboards/app.py

Deploy no Streamlit Cloud
Fork/clone este repositório no GitHub
Em share.streamlit.io: apontar para dashboards/app.py
Copiar deployment/streamlit_cloud/config.toml para .streamlit/config.toml na raiz
Em Settings → Secrets, colar o conteúdo de SECRETS_TEMPLATE.toml preenchido
Clicar "↺ Atualizar dados" na sidebar do app para popular o banco
Nota sobre persistência: o DuckDB no Streamlit Cloud é efêmero — os dados
somem a cada restart do app. Clique "Atualizar dados" sempre que necessário.
Para persistência real entre sessões: migrar para Postgres gerenciado
(Supabase ou Neon — ambos têm free tier suficiente para este projeto).
Sobre o botão "↺ Atualizar dados"
O botão executa etl/run_pipeline.py que:
Extrai dados frescos de todas as APIs configuradas (com retry automático)
Transforma e normaliza para formato tidy (parquet)
Limpa fact_indicator_values (DELETE) e recarrega do zero
O banco não cresce indefinidamente — cada execução resulta no mesmo
volume de dados (truncate + reload). Tempo estimado: 60-120 segundos.
Princípios do projeto
Transparência total: todo placeholder é explicitamente marcado com
explicação do que falta e por quê
Separação rigorosa: evidência empírica ≠ narrativa promocional ≠ projeção
Auditabilidade: toda série documentada em metadata/data_dictionary.py
Honestidade sobre limitações: o WCLI mostra "completeness %",
o Risk Score mostra componentes excluídos e motivo
Referências bibliográficas: Sahm (2019), Estrella & Mishkin (1998),
Caldara & Iacoviello (2022), McNeil et al. (2015) — metodologia rastreável
Bugs conhecidos e status
#
Bug
Severidade
Status
1
TED Spread descontinuado jan/2023
Alta
✅ Corrigido → SOFR
2
MOVE Index instável no yfinance
Alta
✅ Corrigido → FRED BAMLMOVE1WMPIM156
3
Vector StatCan turismo (v1) incorreto
Alta
✅ Corrigido → vector 62370949
4
Natural Gas no mesmo eixo Y do petróleo
Média
✅ Corrigido → eixo Y duplo
5
Duplicação yield curve páginas 02 e 07
Média
✅ Corrigido → separação conceitual
6
Pipeline sem retry logic
Média
✅ Corrigido → retry 2x + backoff 5s
7
Banco crescia a cada atualização
Alta
✅ Corrigido → truncate + reload
8
yfinance MultiIndex columns (v0.2.40+)
Média
✅ Corrigido
9
tests/ vazia
Média
⏳ Pendente

Roadmap — próximas fases
Módulo
Prioridade
Complexidade
GPR Index (Caldara & Iacoviello) — download manual
Alta
Baixa
World Bank API — integrar ao pipeline
Alta
Baixa
DiD / Synthetic Control (contrafactual)
Alta
Alta
WCLI completo (todos os componentes)
Alta
Média
Turismo EUA (NTTO) — download manual
Média
Baixa
Event Study histórico (Copas 2006-2022)
Média
Média
GitHub Actions cron (ETL diário automático)
Média
Baixa
Postgres gerenciado (persistência real)
Média
Média
Testes unitários (pytest)
Média
Baixa
ML Ensemble (XGBoost/LightGBM/Prophet/LSTM)
Baixa
Alta
API FastAPI
Baixa
Média
Edumetria · Eduardo Moraes · 2026