"""
etl/run_pipeline.py
Orquestra o pipeline ETL completo: extractors → transformers → loaders.

Uso local:
    export FRED_API_KEY=... BANXICO_TOKEN=... INEGI_TOKEN=...
    python -m etl.run_pipeline

Uso no Streamlit: chamado via botão na sidebar (ver dashboards/app.py)
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from etl.extractors import fred               # noqa: E402
from etl.extractors import yfinance_markets   # noqa: E402
from etl.extractors import tourism_open_sources  # noqa: E402
from etl.extractors import statcan_macro      # noqa: E402
from etl.extractors import inegi              # noqa: E402

from etl.transformers import clean_macro          # noqa: E402
from etl.transformers import clean_markets        # noqa: E402
from etl.transformers import clean_tourism        # noqa: E402
from etl.transformers import clean_macro_can_mex  # noqa: E402

from etl.loaders import load_indicators       # noqa: E402


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

    try:
        statcan_macro.run()
    except Exception as e:
        log(f"⚠️  Extractor StatCan macro falhou: {e}")

    try:
        inegi.run()
    except Exception as e:
        log(f"⚠️  Extractor INEGI falhou: {e}")

    log("=" * 60)
    log("ETAPA 2/3 — TRANSFORMERS")
    log("=" * 60)

    try:
        clean_macro.run()
    except Exception as e:
        log(f"⚠️  Transformer macro (EUA/FRED) falhou: {e}")

    try:
        clean_markets.run()
    except Exception as e:
        log(f"⚠️  Transformer markets falhou: {e}")

    try:
        clean_tourism.run()
    except Exception as e:
        log(f"⚠️  Transformer turismo falhou: {e}")

    try:
        clean_macro_can_mex.run()
    except Exception as e:
        log(f"⚠️  Transformer macro CAN/MEX falhou: {e}")

    log("=" * 60)
    log("ETAPA 3/3 — LOADERS")
    log("=" * 60)

    try:
        load_indicators.run()
    except Exception as e:
        log(f"⚠️  Loader falhou: {e}")

    log("✅ Pipeline concluído.")


if __name__ == "__main__":
    run()