"""
etl/run_pipeline.py — v4 CORRIGIDO

CORREÇÕES:
- Validação de frescor dos dados (alerta se dados > 60 dias)
- Logging detalhado de sucesso/falha por módulo
- Retry com backoff exponencial por módulo
- Verificação pós-load com detecção de placeholder 100.0
- Fallback gracioso: falha de um módulo não para o pipeline
- Novo: Detecção de dados antigos (últimas datas < 60 dias)
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _safe_run(module, name: str, log=print, retries: int = 2, delay: int = 5) -> bool:
    """Executa módulo com retry e backoff exponencial."""
    for attempt in range(1, retries + 2):
        try:
            module.run()
            return True
        except Exception as e:
            log(f"  ⚠️  [{name}] tentativa {attempt}/{retries + 1}: {e}")
            if attempt <= retries:
                wait_time = delay * (2 ** (attempt - 1))
                log(f"  ⏳ Aguardando {wait_time}s...")
                time.sleep(wait_time)
    log(f"  ✗ [{name}] falhou após {retries + 1} tentativas — continuando")
    return False


def run(log=print):
    """Executa pipeline ETL completo com validações."""
    results = {}

    try:
        from etl.extractors import fred, fred_expanded
        from etl.extractors import yfinance_markets, yfinance_expanded
        from etl.extractors import tourism_open_sources
        from etl.extractors import statcan_macro, bank_of_canada, inegi
    except ImportError as e:
        log(f"⚠️  Erro ao importar extractors: {e}")

    try:
        from etl.transformers import clean_macro, clean_markets, clean_tourism
        from etl.transformers import clean_macro_can_mex, clean_bank_of_canada, clean_expanded
    except ImportError as e:
        log(f"⚠️  Erro ao importar transformers: {e}")

    try:
        from etl.loaders import load_indicators
    except ImportError as e:
        log(f"✗ Erro ao importar loader: {e}")
        return

    # ------------------------------------------------------------------
    # ETAPA 1 — EXTRACTORS
    # ------------------------------------------------------------------
    log("=" * 60)
    log("ETAPA 1/3 — EXTRACTORS")
    log("=" * 60)

    results["FRED"]          = _safe_run(fred,                 "FRED (macro EUA)",            log, retries=2, delay=3)
    results["FRED_exp"]      = _safe_run(fred_expanded,        "FRED Expandido",              log, retries=2, delay=3)
    results["StatCan"]       = _safe_run(statcan_macro,        "StatCan Macro",               log, retries=2, delay=5)
    results["BoC"]           = _safe_run(bank_of_canada,       "Bank of Canada",              log, retries=2, delay=5)
    results["Tourism"]       = _safe_run(tourism_open_sources, "Turismo (StatCan+Banxico)",   log, retries=2, delay=5)
    results["INEGI"]         = _safe_run(inegi,                "INEGI (México)",              log, retries=1, delay=3)

    log("\n  [yfinance] Iniciando (pode levar 30-60s)...")
    results["yfinance"]      = _safe_run(yfinance_markets,     "yfinance (índices, ETFs)",    log, retries=2, delay=15)

    log("\n  [yfinance expanded] Iniciando...")
    results["yfinance_exp"]  = _safe_run(yfinance_expanded,    "yfinance Expandido",          log, retries=2, delay=15)

    # ------------------------------------------------------------------
    # ETAPA 2 — TRANSFORMERS (ordem importa)
    # ------------------------------------------------------------------
    log("\n" + "=" * 60)
    log("ETAPA 2/3 — TRANSFORMERS")
    log("=" * 60)

    results["T_macro"]   = _safe_run(clean_macro,          "Macro EUA",            log)
    results["T_markets"] = _safe_run(clean_markets,        "Markets (yfinance)",   log)
    results["T_tourism"] = _safe_run(clean_tourism,        "Turismo",              log)
    results["T_can_mex"] = _safe_run(clean_macro_can_mex,  "Macro CAN/MEX",        log)
    results["T_boc"]     = _safe_run(clean_bank_of_canada, "Bank of Canada",       log)
    # DEVE ser o último (depende de macro_usa.parquet)
    results["T_expanded"]= _safe_run(clean_expanded,       "Expandido (stress)",   log)

    # ------------------------------------------------------------------
    # ETAPA 3 — LOADER
    # ------------------------------------------------------------------
    log("\n" + "=" * 60)
    log("ETAPA 3/3 — LOADER")
    log("=" * 60)

    results["Loader"] = _safe_run(load_indicators, "Loader principal", log, retries=1)

    # ------------------------------------------------------------------
    # VERIFICAÇÃO PÓS-LOAD
    # ------------------------------------------------------------------
    log("\n" + "=" * 60)
    log("VERIFICAÇÃO PÓS-LOAD")
    log("=" * 60)

    try:
        from database.connection import get_connection
        with get_connection() as conn:
            # Contagem total
            total = conn.execute(
                "SELECT COUNT(*) AS n FROM fact_indicator_values"
            ).df()["n"][0]

            if total == 0:
                log("✗ ALERTA: banco vazio após pipeline!")
                log("  Verifique: (1) chaves de API nos Secrets, "
                    "(2) conectividade, (3) logs acima")
            else:
                log(f"✓ {total:,} registros no banco")

                # ✅ CORREÇÃO 1: Detecta placeholder 100.0
                suspicious = conn.execute("""
                    SELECT indicator_code, COUNT(*) as n
                    FROM fact_indicator_values
                    WHERE value = 100.0
                      AND indicator_code IN (
                        'SP500','VIX','WTI_CRUDE','BRENT_CRUDE','TSX','IPC_MEXICO'
                      )
                    GROUP BY indicator_code
                """).df()

                if not suspicious.empty:
                    log("\n⚠️  Placeholder 100.0 detectado:")
                    for _, row in suspicious.iterrows():
                        log(f"  {row['indicator_code']}: {int(row['n'])} linhas")
                    log("  → Execute novamente ou verifique Yahoo Finance")
                else:
                    log("✓ Nenhum placeholder 100.0 detectado")

                # ✅ CORREÇÃO 2: Verifica frescor dos dados (últimas datas)
                log("\n📅 Verificação de frescor dos dados:")
                freshness = conn.execute("""
                    SELECT 
                        indicator_code,
                        country_code,
                        MAX(period) as last_period,
                        COUNT(*) as n_records
                    FROM fact_indicator_values
                    WHERE is_forecast = FALSE
                    GROUP BY indicator_code, country_code
                    ORDER BY last_period DESC
                """).df()

                if not freshness.empty:
                    freshness["last_period"] = pd.to_datetime(freshness["last_period"])
                    now = datetime.now()
                    freshness["days_old"] = (now - freshness["last_period"]).dt.days
                    
                    # Alertas para dados muito antigos
                    old_data = freshness[freshness["days_old"] > 60]
                    if not old_data.empty:
                        log("\n⚠️  ALERTA: Dados com mais de 60 dias:")
                        for _, row in old_data.iterrows():
                            log(f"  {row['indicator_code']} ({row['country_code']}): "
                                f"{row['days_old']} dias atrás ({row['last_period'].strftime('%Y-%m-%d')})")
                    
                    # Resumo de frescor
                    recent = freshness[freshness["days_old"] <= 7]
                    log(f"\n✓ {len(recent)} indicadores atualizados (≤ 7 dias)")
                    
                    # Últimas datas por país
                    log("\n📊 Últimas datas por país:")
                    for country in ["USA", "CAN", "MEX"]:
                        country_data = freshness[freshness["country_code"] == country]
                        if not country_data.empty:
                            last_date = country_data["last_period"].max()
                            n_indicators = len(country_data)
                            log(f"  {country}: {last_date.strftime('%Y-%m-%d')} ({n_indicators} indicadores)")

    except Exception as e:
        log(f"⚠️  Não foi possível verificar o banco: {e}")

    # ------------------------------------------------------------------
    # RESUMO FINAL
    # ------------------------------------------------------------------
    log("\n" + "=" * 60)
    success = sum(1 for v in results.values() if v)
    total_m = len(results)
    log(f"PIPELINE CONCLUÍDO: {success}/{total_m} módulos com sucesso")
    if success < total_m:
        failed = [k for k, v in results.items() if not v]
        log(f"  Módulos com falha: {failed}")
    log("=" * 60)


if __name__ == "__main__":
    import pandas as pd  # Importa aqui para verificação de frescor
    run()
