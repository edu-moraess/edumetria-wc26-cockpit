# FIFA World Cup 2026™ — Impact Analytics Platform

**Edumetria / Eduardo Moraes | Quant Data Scientist & Economics Researcher**

Plataforma analítica para monitoramento, modelagem e projeção dos impactos
macroeconômicos, geopolíticos, financeiros e sociais da Copa do Mundo FIFA
2026™ (EUA · Canadá · México), horizonte 2026-2035.

Este README documenta a **arquitetura de deploy** (estrutura de pastas,
data layer, ETL, dashboard). Conteúdo analítico (white paper, auditoria
das projeções FIFA, modelagem econométrica, Monte Carlo, WCLI) será
entregue em módulos subsequentes e plugado nesta estrutura.

---

## 1. Estrutura de Pastas

```
fifa2026/
├── config.py                  # configuração central (paths, tema, baseline FIFA, WCLI)
├── requirements.txt
├── data/
│   ├── raw/                    # dados brutos, imutáveis, como recebidos das fontes
│   ├── processed/               # dados limpos/transformados, prontos para modelagem
│   └── external/                 # dados de terceiros (Tourism Economics, STR, FRED, etc.)
├── database/
│   ├── schema.sql               # esquema do Data Warehouse (dimensões + fatos)
│   └── connection.py             # abstração DuckDB (dev) / Postgres (produção)
├── etl/
│   ├── extractors/               # coleta de dados de cada fonte (1 módulo por fonte)
│   ├── transformers/             # limpeza, normalização, cálculo de indicadores derivados
│   └── loaders/                  # carga no Data Warehouse (fact tables)
├── models/
│   ├── econometric/              # I-O, SAM, CGE, DiD, Synthetic Control, GARCH-X, DCC
│   ├── ml/                       # XGBoost, LightGBM, Prophet, LSTM
│   └── montecarlo/                # simulação de cenários (100k+ runs), EVT
├── api/                          # FastAPI — endpoints para servir dados/forecasts
├── dashboards/
│   ├── app.py                    # entry point Streamlit (navegação + tema)
│   ├── components.py             # componentes de UI reutilizáveis (KPI cards, tema Plotly)
│   └── pages/                    # 9 páginas (Executive Overview → Forecast Center)
├── notebooks/                    # exploração, prototipagem de modelos
├── deployment/
│   ├── docker/                   # Dockerfile + docker-compose (app + Postgres + ETL)
│   └── streamlit_cloud/          # config.toml + guia de deploy via Streamlit Community Cloud
└── tests/                         # testes unitários (pytest)
```

### Função de cada diretório

- **data/raw**: snapshot imutável dos dados como chegam das fontes (CSV, JSON, XLSX). Nunca editado manualmente — serve de trilha de auditoria.
- **data/processed**: saída dos `transformers`, já normalizada (unidades consistentes, períodos alinhados), pronta para carga no DW ou consumo direto por modelos.
- **data/external**: datasets de terceiros baixados (Tourism Economics, STR Global, FRED, Goldman Sachs Research, NBER, Brookings) — versionados separadamente por licença/fonte.
- **database**: define e gerencia o Data Warehouse. `schema.sql` é a fonte única de verdade do modelo de dados (star schema: `dim_*` + `fact_*`). `connection.py` permite trocar DuckDB ↔ Postgres via variável de ambiente sem alterar código de negócio.
- **etl/extractors**: um módulo por fonte externa (ex: `fred.py`, `str_global.py`, `tourism_economics.py`, `yfinance_markets.py`). Cada extractor escreve em `data/raw/`.
- **etl/transformers**: lógica de limpeza, conversão de unidades, alinhamento temporal, cálculo de indicadores derivados (ex: PIB incremental líquido = bruto − contrafactual). Escreve em `data/processed/`.
- **etl/loaders**: carrega `data/processed/` nas tabelas `fact_*` do Data Warehouse, com versionamento (`fact_indicator_values.version`).
- **models/econometric**: implementações de Input-Output, SAM, CGE, DiD/Synthetic Control/Event Study/Local Projections (contrafactual), e os modelos GARCH-X/DCC/EVT reaproveitados do Macro Geopolítico Model.
- **models/ml**: ensembles XGBoost/LightGBM/Prophet/LSTM para forecast 2027-2035.
- **models/montecarlo**: motor de simulação (≥100k runs), cálculo de WCLI por cenário, EVT para tail risk.
- **api**: FastAPI servindo os resultados (dashboards podem consumir via API em vez de acesso direto ao DW, facilitando futura integração com outros consumidores — ex: posts institucionais automatizados).
- **dashboards**: aplicação Streamlit. `app.py` define tema/navegação; `pages/` contém as 9 páginas do wireframe; `components.py` centraliza KPI cards e o wrapper de tema Plotly (subplot-safe).
- **deployment**: Dockerfile + compose para ambiente completo (app + Postgres + worker ETL), e guia de deploy gratuito via Streamlit Community Cloud (recomendado para o MVP).
- **tests**: testes unitários para ETL, modelos e cálculo do WCLI.

---

## 2. Arquitetura de Dados

```
Fontes externas (FIFA, Tourism Economics, STR Global, FRED, Goldman Sachs,
NBER, Brookings, yfinance, BCB/SGS, Banxico, StatCan)
        │
        ▼
  data/raw/  ──extractors──►  (snapshot imutável, versionado por data)
        │
        ▼
  etl/transformers  (limpeza, normalização, indicadores derivados,
                      cálculo de impacto líquido/contrafactual)
        │
        ▼
  data/processed/
        │
        ▼
  etl/loaders  ──►  database (DuckDB dev / Postgres produção)
        │                 │
        │                 ├── dim_country, dim_city, dim_indicator,
        │                 │   dim_source, dim_scenario
        │                 ├── fact_indicator_values  (séries observadas + forecast)
        │                 ├── fact_wcli              (WCLI por país/cenário/período)
        │                 ├── fact_montecarlo_*      (distribuições de simulação)
        │                 └── audit_fifa_projections (auditoria das estimativas FIFA)
        │
        ▼
  models/ (econometric, ml, montecarlo)  ──► grava forecasts em fact_indicator_values
        │                                     (is_forecast=TRUE, confidence_low/high)
        ▼
  dashboards/app.py  (Streamlit, 9 páginas)  ◄── api/ (FastAPI, opcional)
```

**Versionamento**: toda linha em `fact_*` tem campo `version` e
`ingested_at`. Atualizações não sobrescrevem — incrementam a versão,
preservando histórico para auditoria (ex: revisão de premissas FIFA).

**Atualizações automáticas**: pipeline ETL roda via cron (GitHub Actions
ou worker dedicado) → atualiza `database/fifa2026.duckdb` (ou Postgres) →
dashboard reflete automaticamente (DuckDB local) ou via API (Postgres).

---

## 3. Como executar localmente

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Inicializar o banco de dados (DuckDB por padrão)
python database/connection.py

# 3. Rodar o dashboard
streamlit run dashboards/app.py
```

---

## 4. Roadmap de Implementação (próximas entregas)

| Módulo | Conteúdo | Status |
|---|---|---|
| Estrutura de deploy | Pastas, config, schema, app Streamlit (9 páginas), Docker, Streamlit Cloud | ✅ Concluído |
| White paper | Executive summary, auditoria FIFA, metodologia (I-O/SAM/CGE/contrafactual), comparação histórica | ⏳ Próxima entrega |
| ETL — extractors | FRED, Tourism Economics, STR Global, yfinance, BCB/SGS, Banxico, StatCan | ⏳ Pendente |
| Modelagem econométrica | GARCH-X/DCC (reaproveitado), DiD/Synthetic Control, Ridge-VAR geopolítico | ⏳ Pendente |
| Monte Carlo + WCLI | Motor de simulação (100k runs), cálculo WCLI por país/cenário | ⏳ Pendente |
| ML Forecast | XGBoost, LightGBM, Prophet, LSTM ensemble | ⏳ Pendente |
| API FastAPI | Endpoints de série/forecast/WCLI | ⏳ Pendente |
| Automação | GitHub Actions cron para ETL diário | ⏳ Pendente |

---

## 5. Sistema de Alertas (proposta — a implementar)

Alertas configuráveis via `fact_indicator_values` + thresholds em
`config.py`:

- **Geopolítico**: GeoFactor Index cruza limiar de regime de estresse → notificação.
- **Mercado**: VIX > threshold ou CAR setorial fora do intervalo de confiança Monte Carlo.
- **Macro**: revisão de PIB/inflação projetado vs. realizado acima de X p.p.
- **Auditoria**: nova versão de projeção FIFA divergente >Y% da versão anterior em `audit_fifa_projections`.

Canal de entrega: e-mail (via API) ou painel dedicado no Streamlit
("Alert Center" — candidato a 10ª página se necessário).
