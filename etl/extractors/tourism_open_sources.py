"""
etl/extractors/tourism_open_sources.py
Extractor de dados de turismo via fontes públicas gratuitas.

CORREÇÃO v2:
- Vector StatCan corrigido: v1 era inválido.
  Série correta: 24-10-0041-01 — International travellers entering Canada
  Vector ID: 62370949 (total chegadas internacionais, mensal)
- Banxico SE39037 mantida (validada)
- Adicionado: Bank of Canada Valet API (macro Canadá, sem token)
"""

import os
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

# ------------------------------------------------------------------
# CANADÁ — StatCan API
# Tabela 24-10-0041-01: International travellers entering Canada
# Vector 62370949 = total chegadas internacionais (mensal)
# Fonte: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2410004101
# ------------------------------------------------------------------
STATCAN_BASE_URL = (
    "https://www150.statcan.gc.ca/t1/wds/rest"
    "/getDataFromVectorsAndLatestNPeriods"
)

STATCAN_TOURISM_VECTORS = {
    "62370949": "chegadas_internacionais_canada_total",
}

# ------------------------------------------------------------------
# MÉXICO — Banxico SIE API
# SE39037 = Llegada de turistas internacionales (total mensual)
# Token gratuito: https://www.banxico.org.mx/SieAPIRest/service/v1/token
# ------------------------------------------------------------------
BANXICO_BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"

BANXICO_TOURISM_SERIES = {
    "SE39037": "turistas_internacionais_mexico",
}


def fetch_statcan_vector(vector_id: str, n_periods: int = 120) -> pd.DataFrame:
    """Busca os últimos N períodos de um vetor StatCan."""
    payload = [{"vectorId": int(vector_id), "latestN": n_periods}]
    resp = requests.post(STATCAN_BASE_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for item in data:
        if item.get("status") != "SUCCESS":
            print(f"  ⚠️  StatCan vector {vector_id}: status={item.get('status')}")
            continue
        for point in item["object"]["vectorDataPoint"]:
            val = point.get("value")
            if val is not None:
                rows.append({"date": point["refPer"], "value": float(val)})

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def fetch_banxico(series_id: str, token: str) -> pd.DataFrame:
    """Busca série completa do Banxico SIE."""
    url     = f"{BANXICO_BASE_URL}/{series_id}/datos"
    headers = {"Bmx-Token": token}
    resp    = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data    = resp.json()

    obs = data["bmx"]["series"][0]["datos"]
    df  = pd.DataFrame(obs)
    df.columns = ["date", "value"]
    df["date"]  = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df["value"] = pd.to_numeric(
        df["value"].astype(str).str.replace(",", ""), errors="coerce"
    )
    return df.dropna()


def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today  = date.today().isoformat()
    frames = []

    # --- Canadá (StatCan) ---
    print("Baixando StatCan — chegadas internacionais Canadá...")
    for vector_id, label in STATCAN_TOURISM_VECTORS.items():
        try:
            df = fetch_statcan_vector(vector_id)
            if df.empty:
                print(f"  ⚠️  Sem dados para vector {vector_id}")
                continue
            df["country"]          = "CAN"
            df["indicator_label"]  = label
            frames.append(df)
            print(f"  → {len(df)} observações (vector {vector_id})")
        except Exception as e:
            print(f"  ⚠️  Erro StatCan vector {vector_id}: {e}")

    # --- México (Banxico) ---
    banxico_token = get_secret("BANXICO_TOKEN")
    if banxico_token:
        for series_id, label in BANXICO_TOURISM_SERIES.items():
            print(f"Baixando Banxico {series_id} ({label})...")
            try:
                df = fetch_banxico(series_id, banxico_token)
                if df.empty:
                    print(f"  ⚠️  Sem dados para {series_id}")
                    continue
                df["country"]         = "MEX"
                df["indicator_label"] = label
                frames.append(df)
                print(f"  → {len(df)} observações")
            except Exception as e:
                print(f"  ⚠️  Erro Banxico {series_id}: {e}")
    else:
        print("  ⚠️  BANXICO_TOKEN não definido — pulando turismo México.")

    print("  ℹ️  EUA (NTTO): sem API automática — ver data/external/ntto_usa/")

    if not frames:
        print("Nenhum dado extraído.")
        return None

    result   = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"tourism_open_sources_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\nSalvo: {out_path} ({len(result):,} linhas)")
    return result


if __name__ == "__main__":
    run()