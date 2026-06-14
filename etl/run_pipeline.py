"""
etl/run_pipeline.py
Orquestra o pipeline ETL completo com retry logic básica.

Uso local:
    python -m etl.run_pipeline
Uso no Streamlit:
    Chamado via botão na sidebar (dashboards/app.py)
"""

import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _safe_run(module, name: str, log=print, retries: int = 2):
    """Executa module.run() com retry simples (backoff 5s)."""
    for attempt in range(1, retries + 2):
        try:
            log(f"🔄 {name} — iniciando (tentativa {attempt})...")
            module.run()
            log(f"✅ {name} — sucesso.")
            return True
        except Exception as e:
            log(f"⚠️ {name} — tentativa {attempt} falhou: {str(e)[:200]}")
            if attempt <= retries:
                log(f"   Aguardando 5 segundos antes da próxima tentativa...")
                time.sleep(5)
            else:
                log(f"✗ {name} — falha definitiva após {retries+1} tentativas.")
    return False


def run(log=print):
    # --- Imports dinâmicos (evita falhar no import se lib ausente) ---
    from etl.extractors import fred
    from etl.extractors import fred_expanded
    from etl.extractors import yfinance_markets
    from etl.extractors import yfinance_expanded
    from etl.extractors import tourism_open_sources
    from etl.extractors import statcan_macro
    from etl.extractors import inegi
    from etl.extractors import bank_of_canada

    from etl.transformers import clean_macro
    from etl.transformers import clean_markets
    from etl.transformers import clean_tourism
    from etl.transformers import clean_macro_can_mex
    from etl.transformers import clean_expanded
    from etl.transformers import clean_bank_of_canada

    from etl.loaders import load_indicators

    log("=" * 60)
    log("ETAPA 1/3 — EXTRACTORS")
    log("=" * 60)

    extractors = [
        (fred,                   "FRED (macro EUA)"),
        (fred_expanded,          "FRED Expandido (stress, recessão)"),
        (yfinance_markets,       "yfinance (índices, ETFs)"),
        (yfinance_expanded,      "yfinance Expandido (NG, Gold, Nasdaq)"),
        (tourism_open_sources,   "Turismo (StatCan + Banxico)"),
        (statcan_macro,          "StatCan Macro"),
        (inegi,                  "INEGI (México)"),
        (bank_of_canada,         "Bank of Canada"),
    ]

    for module, name in extractors:
        _safe_run(module, name, log)

    log("")
    log("=" * 60)
    log("ETAPA 2/3 — TRANSFORMERS")
    log("=" * 60)

    transformers = [
        (clean_macro,          "Macro EUA (FRED)"),
        (clean_markets,        "Markets (yfinance)"),
        (clean_tourism,        "Turismo"),
        (clean_macro_can_mex,  "Macro CAN/MEX"),
        (clean_expanded,       "Expandido (stress, recessão)"),
        (clean_bank_of_canada, "Bank of Canada"),
    ]

    for module, name in transformers:
        _safe_run(module, name, log)

    log("")
    log("=" * 60)
    log("ETAPA 3/3 — LOADERS")
    log("=" * 60)

    _safe_run(load_indicators, "Loader principal", log)

    log("")
    log("✅ Pipeline concluído.")


if __name__ == "__main__":
    run()