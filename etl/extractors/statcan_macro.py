"""
etl/extractors/statcan_macro.py
Extractor de dados macroeconômicos do Canadá via StatCan API (gratuita).

Indicadores:
- PIB trimestral
- Inflação (CPI)
- Desemprego

API: https://www150.statcan.gc.ca/n1/pub/71-607-x/71-607-x2018005-eng.htm
Sem token necessário.
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

STATCAN_URL = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods"

# Vetores StatCan -> (indicator_code, descrição)
STATCAN_MACRO_VECTORS = {
    "v62305752": ("GDP_REAL_CAN", "PIB Real Canadá (trimestral)"),
    "v41690973": ("CPI_CAN", "CPI Canadá (inflação)"),
    "v2064705": ("UNEMPLOYMENT_RATE_CAN", "Taxa de Desemprego Canadá"),
    "v39079": ("POLICY_RATE_CAN", "Taxa de Política Monetária — BoC"),
}


def fetch_statcan_vector(vector_id: str, n_periods: int = 80) -> pd.DataFrame:
    payload = [{"vectorId": vector_id.replace("v", ""), "latestN": n_periods}]
    resp = requests.post(STATCAN_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for item in data:
        if item.get("status") != "SUCCESS":
            continue
        for point in item["object"]["vectorDataPoint"]:
            rows.append({"date": point["refPer"], "value": point["value"]})
    return pd.DataFrame(rows)


def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    for vector_id, (code, label) in STATCAN_MACRO_VECTORS.items():
        try:
            print(f"Baixando StatCan {vector_id} ({label})...")
            df = fetch_statcan_vector(vector_id)
            if df.empty:
                print(f"  ⚠️  Sem dados para {vector_id}")
                continue
            df["indicator_label"] = code
            df["country"] = "CAN"
            frames.append(df)
        except Exception as e:
            print(f"  ⚠️  Erro StatCan {vector_id}: {e}")

    if not frames:
        print("Nenhum dado extraído do StatCan macro.")
        return None

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"statcan_macro_can_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} ({len(result)} linhas)")
    return result


if __name__ == "__main__":
    run() 