"""
etl/extractors/inegi.py
Extractor de dados macroeconômicos do México via INEGI API (gratuita).

Indicadores:
- PIB trimestral (variação %)
- Inflação (INPC)
- Desemprego (ETOE)

Documentação: https://www.inegi.org.mx/servicios/api_indicadores.html
Token: solicitado em https://www.inegi.org.mx/app/api/indicadores/interna/
       (gratuito, aprovação automática)
"""

import sys
from pathlib import Path
from datetime import date

import requests
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR  # noqa: E402
from config_secrets import get_secret  # noqa: E402

INEGI_BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"

# Série -> (indicator_code interno, descrição)
INEGI_SERIES = {
    "444579": ("GDP_REAL_MEX", "PIB Real México (variação trimestral %)"),
    "628194": ("CPI_MEX", "INPC México (inflação)"),
    "444612": ("UNEMPLOYMENT_RATE_MEX", "Taxa de Desemprego México"),
}


def fetch_inegi(series_id: str, token: str) -> pd.DataFrame:
    url = f"{INEGI_BASE_URL}/{series_id}/es/BIE/2/es/false/xml"
    params = {"token": token}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()

    # INEGI retorna XML — parse manual simples
    from xml.etree import ElementTree as ET
    root = ET.fromstring(resp.content)
    ns = {"ns": "http://www.inegi.org.mx/indicadores"}

    rows = []
    for obs in root.findall(".//ns:Obs", ns):
        period = obs.attrib.get("TIME_PERIOD", "")
        value = obs.attrib.get("OBS_VALUE", "")
        if period and value:
            rows.append({"date": period, "value": float(value)})

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def run():
    token = get_secret("INEGI_TOKEN")
    if not token:
        print("⚠️  INEGI_TOKEN não definido — pulando México (INEGI).")
        print("     Obter em: https://www.inegi.org.mx/app/api/indicadores/interna/")
        return None

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    for series_id, (code, label) in INEGI_SERIES.items():
        try:
            print(f"Baixando INEGI {series_id} ({label})...")
            df = fetch_inegi(series_id, token)
            if df.empty:
                print(f"  ⚠️  Sem dados para {series_id}")
                continue
            df["indicator_label"] = code
            df["country"] = "MEX"
            frames.append(df)
        except Exception as e:
            print(f"  ⚠️  Erro INEGI {series_id}: {e}")

    if not frames:
        return None

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"inegi_macro_mex_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} ({len(result)} linhas)")
    return result


if __name__ == "__main__":
    run()