"""
etl/run_pipeline.py
Orquestra o pipeline ETL completo: extractors → transformers → loaders.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Verificação antecipada do config
try:
    from config import DB_DIR  # noqa: F401
except ImportError as e:
    print(f"ERRO CRÍTICO: Não foi possível importar 'config'. Verifique o sys.path. Detalhe: {e}")
    sys.exit(1)

from etl.extractors import fred, yfinance_markets, tourism_open_sources
from etl.transformers import clean_macro, clean_markets, clean_tourism
from etl.loaders import load_indicators


def run(log=print):
    log("=" * 60)
    log("ETAPA 1/3 — EXTRACTORS")
    log("=" * 60)

    try:
        fred.run()
    except Exception as e:
        log(f"⚠️  Extractor FRED falhou: {e}")

    try:
        yfinance_markets.run()
    except Exception as e:
        log(f"⚠️  Extractor yfinance falhou: {e}")

    try:
        tourism_open_sources.run()
    except Exception as e:
        log(f"⚠️  Extractor turismo falhou: {e}")

    log("ETAPA 2/3 — TRANSFORMERS")

    try:
        clean_macro.run()
    except Exception as e:
        log(f"⚠️  Transformer macro falhou: {e}")

    try:
        clean_markets.run()
    except Exception as e:
        log(f"⚠️  Transformer markets falhou: {e}")

    try:
        clean_tourism.run()
    except Exception as e:
        log(f"⚠️  Transformer turismo falhou: {e}")

    log("ETAPA 3/3 — LOADERS")
    load_indicators.run()

    log("✅ Pipeline concluído.")


if __name__ == "__main__":
    run()