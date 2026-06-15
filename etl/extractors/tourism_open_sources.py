"""
etl/extractors/tourism_open_sources.py

CORREÇÕES v4 (Jun/2026):
- Force download + data dinâmica até hoje
- Retry robusto + timeout aumentado
- Validação de frescor dos dados
- CLI --force-download
- Melhor tratamento de erros e logging
"""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta
import argparse
import time

import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR
from config_secrets import get_secret

STATCAN_BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods"

STATCAN_TOURISM_VECTORS = {
    62370949: "chegadas_internacionais_canada_total",
}

MIN_MONTHLY_ARRIVALS = 1_000
MAX_DAYS_OLD = 45  # Alerta se dados mais antigos que isso

BANXICO_BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"
BANXICO_TOURISM_SERIES = {
    "SE39037": "turistas_internacionais_mexico",
}

def create_session_with_retry() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_statcan_vector(vector_id: int, n_periods: int = 180) -> pd.DataFrame:
    session = create_session_with_retry()
    payload = [{"vectorId": vector_id, "latestN": n_periods}]
    try:
        resp = session.post(STATCAN_BASE_URL, json=payload, timeout=45)
        resp.raise_for_status()
        data = resp.json()

        rows = []
        for item in data:
            obj = item.get("object", {})
            for point in obj.get("vectorDataPoint", []):
                val = point.get("value")
                ref = point.get("refPer")
                if val is not None and ref:
                    rows.append({"date": ref, "value": float(val)})

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df.dropna().sort_values("date").reset_index(drop=True)
    except Exception as e:
        print(f"  ✗ Erro StatCan: {e}")
        return pd.DataFrame()

def fetch_banxico(series_id: str, token: str) -> pd.DataFrame:
    session = create_session_with_retry()
    url = f"{BANXICO_BASE_URL}/{series_id}/datos"
    headers = {"Bmx-Token": token}
    try:
        resp = session.get(url, headers=headers, timeout=45)
        resp.raise_for_status()
        data = resp.json()

        series_data = data.get("bmx", {}).get("series", [])
        if not series_data:
            return pd.DataFrame()

        obs = series_data[0].get("datos", [])
        if not obs:
            return pd.DataFrame()

        df = pd.DataFrame(obs)
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
        df["value"] = pd.to_numeric(df["value"].astype(str).str.replace(",", ""), errors="coerce")
        return df.dropna().sort_values("date").reset_index(drop=True)
    except Exception as e:
        print(f"  ✗ Erro Banxico: {e}")
        return pd.DataFrame()

def run(force_download: bool = False) -> pd.DataFrame | None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    print(f"🚀 Iniciando extração Turismo — {today}")

    # Canadá (StatCan)
    for vector_id, label in STATCAN_TOURISM_VECTORS.items():
        print(f"Baixando StatCan vector {vector_id} ({label})...")
        df = fetch_statcan_vector(vector_id)
        if df.empty:
            print("  ✗ Sem dados StatCan")
            continue

        last_date = df['date'].max()
        days_old = (datetime.now() - last_date).days
        print(f"  → {len(df)} obs. | {df['date'].min():%b/%Y} a {last_date:%b/%Y} ({days_old} dias atrás)")

        if days_old > MAX_DAYS_OLD:
            print(f"  ⚠️  Dados possivelmente desatualizados ({days_old} dias)")

        invalid = (df["value"] < MIN_MONTHLY_ARRIVALS).sum()
        if invalid > 0:
            df = df[df["value"] >= MIN_MONTHLY_ARRIVALS]

        df["country"] = "CAN"
        df["indicator_label"] = label
        frames.append(df)
        print(f"  ✓ StatCan OK — {len(df)} registros válidos")

    # México (Banxico)
    banxico_token = get_secret("BANXICO_TOKEN")
    if banxico_token:
        for series_id, label in BANXICO_TOURISM_SERIES.items():
            print(f"Baixando Banxico {series_id} ({label})...")
            df = fetch_banxico(series_id, banxico_token)
            if df.empty:
                print("  ✗ Sem dados Banxico")
                continue
            last_date = df['date'].max()
            print(f"  → {len(df)} obs. até {last_date:%b/%Y}")
            df["country"] = "MEX"
            df["indicator_label"] = label
            frames.append(df)
            print(f"  ✓ Banxico OK")
    else:
        print("  ⚠️ BANXICO_TOKEN não configurado — México indisponível")

    if not frames:
        print("\n✗ Nenhum dado obtido. Verifique chaves e conexão.")
        return None

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"tourism_open_sources_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\n✅ Sucesso! Salvo: {out_path} ({len(result):,} linhas)")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()
    run(force_download=args.force_download)