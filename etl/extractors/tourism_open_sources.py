"""
etl/extractors/tourism_open_sources.py
Extractor de dados de turismo via fontes públicas/gratuitas.

- StatCan (Canadá): API REST aberta, sem chave
- Banxico (México): requer BANXICO_TOKEN (Secrets ou .env)
- EUA (NTTO): sem API — download manual, ver data/external/ntto_usa/
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

STATCAN_BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods"

STATCAN_VECTORS = {
    "v1": "chegadas_internacionais_canada_total",
}


def fetch_statcan(vector_id: str, n_periods: int = 60) -> pd.DataFrame:
    payload = [{"vectorId": vector_id.replace("v", ""), "latestN": n_periods}]
    resp = requests.post(STATCAN_BASE_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for item in data:
        if item.get("status") != "SUCCESS":
            continue
        for point in item["object"]["vectorDataPoint"]:
            rows.append({"date": point["refPer"], "value": point["value"]})
    return pd.DataFrame(rows)


BANXICO_BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"

BANXICO_SERIES = {
    "SE39037": "turistas_internacionais_mexico",
}


def fetch_banxico(series_id: str, token: str) -> pd.DataFrame:
    url = f"{BANXICO_BASE_URL}/{series_id}/datos"
    headers = {"Bmx-Token": token}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    obs = data["bmx"]["series"][0]["datos"]
    df = pd.DataFrame(obs)
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df["value"] = pd.to_numeric(
        df["value"].astype(str).str.replace(",", ""), errors="coerce"
    )
    return df.dropna()


def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    for vector_id, label in STATCAN_VECTORS.items():
        try:
            print(f"Baixando StatCan {vector_id} ({label})...")
            df = fetch_statcan(vector_id)
            df["country"] = "CAN"
            df["indicator_label"] = label
            frames.append(df)
        except Exception as e:
            print(f"  ⚠️  Erro StatCan {vector_id}: {e}")

    banxico_token = get_secret("BANXICO_TOKEN")
    if banxico_token:
        for series_id, label in BANXICO_SERIES.items():
            try:
                print(f"Baixando Banxico {series_id} ({label})...")
                df = fetch_banxico(series_id, banxico_token)
                df["country"] = "MEX"
                df["indicator_label"] = label
                frames.append(df)
            except Exception as e:
                print(f"  ⚠️  Erro Banxico {series_id}: {e}")
    else:
        print("  ⚠️  BANXICO_TOKEN não definido — pulando México.")

    print("  ℹ️  EUA (NTTO): sem API automática.")

    if not frames:
        print("Nenhum dado extraído.")
        return None

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"tourism_open_sources_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} ({len(result)} linhas)")
    return result


if __name__ == "__main__":
    run()