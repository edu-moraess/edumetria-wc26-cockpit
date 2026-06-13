# Deploy — Streamlit Community Cloud

## Passos

1. Subir o repositório `edumetria-wc26-cockpit/` para o GitHub.
2. Em https://share.streamlit.io, criar novo app:
   - Repository: seu repo
   - Branch: main
   - Main file path: `dashboards/app.py`
3. Garantir que `.streamlit/config.toml` existe na raiz (cópia de
   `deployment/streamlit_cloud/config.toml`).
4. Variáveis de ambiente (Secrets):
   - `FIFA2026_DB_BACKEND = "duckdb"` (recomendado para o MVP)
   - Se usar Postgres gerenciado (Supabase, Neon):
     `FIFA2026_POSTGRES_URL = "postgresql://..."`
     `FIFA2026_DB_BACKEND = "postgres"`

## Limitações do tier gratuito

- Builds com `prophet`, `lightgbm`, `torch` podem demorar (compilação)
  e dar timeout. Para o MVP inicial, remover essas libs do
  `requirements.txt` e adicionar apenas quando os modelos forem
  efetivamente integrados.
- DuckDB funciona bem como banco local read-mostly.

## Atualização automática (proposta futura)

GitHub Actions com cron diário:
1. Roda `python -m etl.run_pipeline`
2. Atualiza `database/fifa2026.duckdb`
3. Commit automático do arquivo atualizado
4. Streamlit Cloud detecta push e faz redeploy automático
