"""
etl/run_pipeline.py
Orquestra o pipeline ETL completo: extractors → transformers → loaders.

Uso:
    python -m etl.run_pipeline
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from etl.extractors import fred, yfinance_markets, tourism_open_sources  # noqa: E402
from etl.transformers import clean_macro, clean_markets, clean_tourism  # noqa: E402
from etl.loaders import load_indicators  # noqa: E402


def run():
    print("=" * 60)
    print("ETAPA 1/3 — EXTRACTORS")
    print("=" * 60)

    try:
        fred.run()
    except Exception as e:
        print(f"⚠️  Extractor FRED falhou: {e}")

    try:
        yfinance_markets.run()
    except Exception as e:
        print(f"⚠️  Extractor yfinance falhou: {e}")

    try:
        tourism_open_sources.run()
    except Exception as e:
        print(f"⚠️  Extractor turismo falhou: {e}")

    print("\n" + "=" * 60)
    print("ETAPA 2/3 — TRANSFORMERS")
    print("=" * 60)

    try:
        clean_macro.run()
    except Exception as e:
        print(f"⚠️  Transformer macro falhou: {e}")

    try:
        clean_markets.run()
    except Exception as e:
        print(f"⚠️  Transformer markets falhou: {e}")

    try:
        clean_tourism.run()
    except Exception as e:
        print(f"⚠️  Transformer turismo falhou: {e}")

    print("\n" + "=" * 60)
    print("ETAPA 3/3 — LOADERS")
    print("=" * 60)

    load_indicators.run()

    print("\n✅ Pipeline concluído.")


if __name__ == "__main__":
    run()
