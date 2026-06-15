"""
etl/extractors/tourism_open_sources.py

CORREÇÕES v3:
- Vector StatCan corrigido: 62370949
  (tabela 24-10-0041-01 — chegadas internacionais ao Canadá, mensal)
  O vector "v1" anterior retornava série de 2011-2012 (errado)
- Validação: rejeita valores < 1.000 (chegadas reais > 100.000/mês)
- Banxico SE39037 mantida e validada
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

STATCAN_BASE_URL = (
    "https://www150.statcan.gc.ca/t1/wds/rest"
    "/getDataFromVectorsAndLatestNPeriods"
)

STATCAN_TOURISM_VECTORS = {
    62370949: "chegadas_internacionais_canada_total",
}

MIN_MONTHLY_ARRIVALS = 1_000

BANXICO_BASE_URL     = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"
BANXICO_TOURISM_SERIES = {
    "SE39037": "turistas_internacionais_mexico",
}


def fetch_statcan_vector(vector_id: int, n_periods: int = 120) -> pd.DataFrame:
    payload = [{"vectorId": vector_id, "latestN": n_periods}]
    resp = requests.post(STATCAN_BASE_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for item in data:
        obj        = item.get("object", {})
        data_points = obj.get("vectorDataPoint", [])
        for point in data_points:
            val = point.get("value")
            ref = point.get("refPer")
            if val is not None and ref:
                rows.append({"date": ref, "value": float(val)})

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def fetch_banxico(series_id: str, token: str) -> pd.DataFrame:
    url     = f"{BANXICO_BASE_URL}/{series_id}/datos"
    headers = {"Bmx-Token": token}
    resp    = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data    = resp.json()

    series_data = data.get("bmx", {}).get("series", [])
    if not series_data:
        return pd.DataFrame()

    obs = series_data[0].get("datos", [])
    if not obs:
        return pd.DataFrame()

    df = pd.DataFrame(obs)
    df.columns = ["date", "value"]
    df["date"]  = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df["value"] = pd.to_numeric(
        df["value"].astype(str).str.replace(",", ""), errors="coerce"
    )
    return df.dropna()


def run() -> pd.DataFrame | None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today  = date.today().isoformat()
    frames = []

    # --- Canadá (StatCan vector 62370949) ---
    for vector_id, label in STATCAN_TOURISM_VECTORS.items():
        print(f"Baixando StatCan vector {vector_id} ({label})...")
        try:
            df = fetch_statcan_vector(vector_id)
            if df.empty:
                print(f"  ✗ Sem dados para vector {vector_id}")
                continue

            print(f"  → {len(df)} obs. | {df['date'].min().strftime('%b/%Y')} a {df['date'].max().strftime('%b/%Y')}")
            print(f"  → Último valor: {df['value'].iloc[-1]:,.0f}")

            invalid = (df["value"] < MIN_MONTHLY_ARRIVALS).sum()
            if invalid > 0:
                print(f"  ⚠️  {invalid} linhas < {MIN_MONTHLY_ARRIVALS} removidas")
                df = df[df["value"] >= MIN_MONTHLY_ARRIVALS]

            if len(df) < 12:
                print(f"  ✗ Dados insuficientes ({len(df)} obs.) — pulando")
                continue

            df["country"]         = "CAN"
            df["indicator_label"] = label
            frames.append(df)
            print(f"  ✓ {len(df)} observações válidas")

        except Exception as e:
            print(f"  ✗ Erro StatCan vector {vector_id}: {e}")

    # --- México (Banxico) ---
    banxico_token = get_secret("BANXICO_TOKEN")
    if banxico_token:
        for series_id, label in BANXICO_TOURISM_SERIES.items():
            print(f"Baixando Banxico {series_id} ({label})...")
            try:
                df = fetch_banxico(series_id, banxico_token)
                if df.empty:
                    print(f"  ✗ Sem dados para {series_id}")
                    continue
                print(f"  → {len(df)} obs. | {df['date'].min().strftime('%b/%Y')} a {df['date'].max().strftime('%b/%Y')}")
                df["country"]         = "MEX"
                df["indicator_label"] = label
                frames.append(df)
                print(f"  ✓ {len(df)} observações válidas")
            except Exception as e:
                print(f"  ✗ Erro Banxico {series_id}: {e}")
    else:
        print("  ⚠️  BANXICO_TOKEN não definido — turismo México indisponível")

    if not frames:
        print("\n✗ Nenhum dado de turismo obtido.")
        return None

    result   = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"tourism_open_sources_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\n✓ Salvo: {out_path} ({len(result):,} linhas)")
    return result


if __name__ == "__main__":
    run()