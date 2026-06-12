# ARVORE DO PROJETO — FIFA 2026 Impact Analytics Platform

Guia de orientação: onde cada coisa mora e por quê. Use este arquivo
como mapa sempre que for adicionar um arquivo novo e não souber onde
colocar.

```
fifa2026/
│
├── config.py                  ⚙️  Configuração central — ÚNICA fonte de
│                                  verdade para: paths, baseline FIFA,
│                                  pesos do WCLI, cores/tema, horizonte
│                                  temporal. Tudo que for "parâmetro
│                                  global" entra aqui, nunca hardcoded
│                                  em outro arquivo.
│
├── requirements.txt           📦  Dependências Python (pip)
├── .env.example                🔑  Modelo de variáveis de ambiente
│                                  (copiar para .env, nunca commitar .env)
├── .gitignore
├── README.md                   📖  Arquitetura geral + roadmap
│
├── data/                       💾  ARMAZENAMENTO DE ARQUIVOS (não código)
│   ├── raw/                       → dados crus, exatamente como vieram
│   │                                 da fonte (CSV/JSON/XLSX). Nunca editar
│   │                                 manualmente. É a "prova" para auditoria.
│   ├── processed/                 → dados já limpos/normalizados pelos
│   │                                 transformers, prontos para carregar
│   │                                 no banco ou alimentar modelos direto.
│   └── external/                  → datasets de terceiros baixados
│                                     (Tourism Economics, STR Global, FRED,
│                                     relatórios FIFA, etc.)
│
├── database/                   🗄️  TUDO relacionado ao Data Warehouse
│   ├── schema.sql                  → definição das tabelas (dim_* e fact_*).
│   │                                 Fonte única de verdade do modelo de dados.
│   └── connection.py               → função get_connection() que abre
│                                     DuckDB (dev) ou Postgres (produção)
│                                     dependendo de FIFA2026_DB_BACKEND.
│
├── etl/                         🔄  PIPELINE DE DADOS (Extract-Transform-Load)
│   ├── extractors/                 → 1 arquivo por FONTE EXTERNA.
│   │                                 Ex: fred.py, str_global.py,
│   │                                 tourism_economics.py, yfinance_markets.py,
│   │                                 bcb_sgs.py, banxico.py, statcan.py
│   │                                 Cada um: baixa dados → grava em data/raw/
│   │
│   ├── transformers/               → 1 arquivo por TIPO DE TRANSFORMAÇÃO.
│   │                                 Ex: clean_macro.py, fx_normalization.py,
│   │                                 net_impact_calculator.py (bruto → líquido
│   │                                 → contrafactual)
│   │                                 Lê data/raw/ → grava data/processed/
│   │
│   └── loaders/                    → grava data/processed/ nas tabelas
│                                     fact_* do banco (com versionamento).
│                                     Ex: load_indicators.py, load_wcli.py
│
├── models/                      🧮  TODA A MODELAGEM QUANTITATIVA
│   ├── econometric/                 → Input-Output, SAM, CGE,
│   │                                 DiD / Synthetic Control / Event Study
│   │                                 (contrafactual), GARCH-X, DCC, Ridge-VAR
│   │                                 (reaproveitado do Macro Geopolítico Model)
│   │
│   ├── ml/                          → XGBoost, LightGBM, Prophet, LSTM
│   │                                 (forecast 2027-2035)
│   │
│   └── montecarlo/                  → motor de simulação (100k+ runs),
│                                     cálculo do WCLI por cenário, EVT
│                                     (tail risk / riscos extremos)
│
├── api/                          🌐  FastAPI — expõe os resultados
│                                     (séries, forecasts, WCLI) via endpoints
│                                     REST. Opcional para o MVP; útil quando
│                                     outros consumidores (ex: gerador de
│                                     posts institucionais) precisarem dos
│                                     dados sem acessar o banco direto.
│
├── dashboards/                   📊  APLICAÇÃO STREAMLIT (o que o usuário vê)
│   ├── app.py                       → entry point. Define tema CSS,
│   │                                 sidebar institucional, navegação
│   │                                 entre as 9 páginas.
│   │
│   ├── components.py                → peças de UI reutilizáveis:
│   │                                 kpi_card(), kpi_row(), page_header(),
│   │                                 apply_theme() (wrapper Plotly
│   │                                 subplot-safe), data_pending_notice()
│   │
│   └── pages/                       → 1 arquivo por página do wireframe:
│       ├── 01_executive_overview.py
│       ├── 02_macroeconomia.py
│       ├── 03_turismo.py
│       ├── 04_aviacao.py
│       ├── 05_hotelaria.py
│       ├── 06_mercado_financeiro.py
│       ├── 07_geopolitica.py
│       ├── 08_esg.py
│       └── 09_forecast_center.py
│
├── notebooks/                    📓  Jupyter notebooks — exploração e
│                                     prototipagem ANTES de promover o
│                                     código para etl/ ou models/.
│                                     Nada daqui vai para produção direto.
│
├── deployment/                   🚀  Tudo sobre COMO COLOCAR NO AR
│   ├── docker/
│   │   ├── Dockerfile               → imagem da aplicação
│   │   └── docker-compose.yml       → app + Postgres + worker ETL juntos
│   │
│   └── streamlit_cloud/
│       ├── config.toml              → tema (copiar para .streamlit/config.toml)
│       └── DEPLOY.md                → passo a passo deploy gratuito
│
└── tests/                         ✅  Testes automatizados (pytest)
                                       1 arquivo de teste por módulo de
                                       etl/ ou models/. Ex:
                                       test_net_impact_calculator.py,
                                       test_wcli.py
```

---

## REGRAS DE SEPARAÇÃO — "ONDE EU COLOCO ISSO?"

| Se você está escrevendo... | Vai em... |
|---|---|
| Um parâmetro novo (peso, cor, ano, threshold) | `config.py` |
| Código que baixa dados de uma fonte nova | `etl/extractors/<fonte>.py` |
| Código que limpa/transforma/calcula indicador derivado | `etl/transformers/<tipo>.py` |
| Código que grava no banco | `etl/loaders/<tabela>.py` |
| Nova tabela ou coluna no banco | `database/schema.sql` |
| Modelo estatístico/econométrico (GARCH, VAR, DiD...) | `models/econometric/` |
| Modelo de ML (XGBoost, LSTM...) | `models/ml/` |
| Simulação Monte Carlo / WCLI / EVT | `models/montecarlo/` |
| Nova página do dashboard | `dashboards/pages/NN_nome.py` |
| Componente de UI usado em 2+ páginas | `dashboards/components.py` |
| Endpoint para outros sistemas consumirem | `api/` |
| Exploração rápida, "vou tentar uma ideia" | `notebooks/` (promover depois) |
| Teste de qualquer módulo acima | `tests/test_<modulo>.py` |

---

## FLUXO DE UMA NOVA FONTE DE DADOS (exemplo prático)

Digamos que você vá integrar dados da **STR Global** (hotelaria):

1. `etl/extractors/str_global.py` — baixa CSV/API → salva em `data/raw/str_global_YYYYMMDD.csv`
2. `etl/transformers/clean_hotel_data.py` — lê `data/raw/str_global_*`, normaliza unidades (USD, %), alinha datas → salva em `data/processed/hotel_indicators.parquet`
3. `etl/loaders/load_indicators.py` — lê `data/processed/hotel_indicators.parquet` → insere em `fact_indicator_values` (categoria `hotelaria`, fonte `STR Global`)
4. `dashboards/pages/05_hotelaria.py` — já está pronta; só troca os `data_pending_notice()` por query real via `database/connection.py`

Nenhum desses passos exige tocar nos outros módulos — é exatamente essa
independência que permite trabalhar em paralelo (ex: você desenvolvendo
o white paper enquanto eu evoluo o ETL).

---

## ORDEM SUGERIDA DE IMPLEMENTAÇÃO (20 dias)

1. **schema.sql + connection.py** já prontos ✅
2. `etl/extractors/` para as fontes mais críticas primeiro:
   FIFA baseline (já em config.py) → FRED (macro) → yfinance (mercado financeiro)
3. `models/econometric/net_impact.py` — cálculo bruto/líquido/contrafactual (alimenta página 1)
4. `models/montecarlo/wcli.py` — WCLI (alimenta página 1 e 9)
5. `etl/loaders/` ligando tudo ao banco
6. Trocar `data_pending_notice()` por queries reais, página por página, na ordem do wireframe (01 → 09)
7. `models/ml/` (ensemble) por último — é o que exige mais tempo de treino/validação
