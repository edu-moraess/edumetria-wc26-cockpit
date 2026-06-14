"""
etl/run_pipeline.py
Orquestra o pipeline ETL completo.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from etl.extractors import fred                  # noqa: E402
from etl.extractors import fred_expanded         # noqa: E402
from etl.extractors import yfinance_markets      # noqa: E402
from etl.extractors import yfinance_expanded     # noqa: E402
from etl.extractors import tourism_open_sources  # noqa: E402
from etl.extractors import statcan_macro         # noqa: E402
from etl.extractors import inegi                 # noqa: E402

from etl.transformers import clean_macro          # noqa: E402
from etl.transformers import clean_markets        # noqa: E402
from etl.transformers import clean_tourism        # noqa: E402
from etl.transformers import clean_macro_can_mex  # noqa: E402
from etl.transformers import clean_expanded       # noqa: E402

from etl.loaders import load_indicators           # noqa: E402


def run(log=print):
    log("=" * 60)
    log("ETAPA 1/3 — EXTRACTORS")
    log("=" * 60)

    for name, module in [
        ("FRED",            fred),
        ("FRED expandido",  fred_expanded),
        ("yfinance",        yfinance_markets),
        ("yfinance expandido", yfinance_expanded),
        ("Turismo",         tourism_open_sources),
        ("StatCan macro",   statcan_macro),
        ("INEGI",           inegi),
    ]:
        try:
            module.run()
        except Exception as e:
            log(f"⚠️  Extractor {name} falhou: {e}")

    log("=" * 60)
    log("ETAPA 2/3 — TRANSFORMERS")
    log("=" * 60)

    for name, module in [
        ("Macro EUA",        clean_macro),
        ("Markets",          clean_markets),
        ("Turismo",          clean_tourism),
        ("Macro CAN/MEX",    clean_macro_can_mex),
        ("Expandido",        clean_expanded),
    ]:
        try:
            module.run()
        except Exception as e:
            log(f"⚠️  Transformer {name} falhou: {e}")

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