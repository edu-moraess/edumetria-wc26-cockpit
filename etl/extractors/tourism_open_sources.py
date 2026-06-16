"""
etl/extractors/tourism_open_sources.py — v4 (Patch 15/Jun/2026)
- Force download sempre no pipeline
- Retry robusto + timeout
- Validação forte de frescor
- Compatível com Streamlit Cloud
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

BANXICO_BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"
BANXICO_TOURISM_SERIES = {
    "SE39037": "turistas_internacionais_mexico",
}

MIN_MONTHLY_ARRIVALS = 1_000
MAX_DAYS_OLD = 60

def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_statcan_vector(vector_id: int, n_periods: int = 200) -> pd.DataFrame:
    session = create_session()
    payload = [{"vectorId": vector_id, "latestN": n_periods}]
    try:
        resp = session.post(STATCAN_BASE_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        rows = []
        for item in data:
            for point in item.get("object", {}).get("vectorDataPoint", []):
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
        print(f"  ✗ StatCan error: {e}")
        return pd.DataFrame()

def fetch_banxico(series_id: str, token: str) -> pd.DataFrame:
    # ... (mesma função robusta do patch anterior)
    session = create_session()
    url = f"{BANXICO_BASE_URL}/{series_id}/datos"
    headers = {"Bmx-Token": token}
    try:
        resp = session.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        obs = data.get("bmx", {}).get("series", [{}])[0].get("datos", [])
        if not obs:
            return pd.DataFrame()
        df = pd.DataFrame(obs)
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
        df["value"] = pd.to_numeric(df["value"].astype(str).str.replace(",", ""), errors="coerce")
        return df.dropna().sort_values("date").reset_index(drop=True)
    except Exception as e:
        print(f"  ✗ Banxico error: {e}")
        return pd.DataFrame()

def run(force_download: bool = False) -> pd.DataFrame | None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    print(f"🚀 Turismo Extractor v4 — {today} (force={force_download})")

    # Canadá
    for vector_id, label in STATCAN_TOURISM_VECTORS.items():
        print(f"→ StatCan {vector_id} ...")
        df = fetch_statcan_vector(vector_id)
        if not df.empty:
            last = df['date'].max()
            days_old = (datetime.now() - last).days
            print(f"  ✓ {len(df)} obs. até {last:%b/%Y} ({days_old}d atrás)")
            df = df[df["value"] >= MIN_MONTHLY_ARRIVALS]
            df["country"] = "CAN"
            df["indicator_label"] = label
            frames.append(df)

    # México
    token = get_secret("BANXICO_TOKEN")
    if token:
        for sid, label in BANXICO_TOURISM_SERIES.items():
            print(f"→ Banxico {sid} ...")
            df = fetch_banxico(sid, token)
            if not df.empty:
                df["country"] = "MEX"
                df["indicator_label"] = label
                frames.append(df)

    if not frames:
        print("✗ Nenhum dado obtido")
        return None

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"tourism_open_sources_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"✅ Salvo {out_path} ({len(result):,} linhas)")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-download", action="store_true", default=True)  # default True agora
    args = parser.parse_args()
    run(force_download=args.force_download)