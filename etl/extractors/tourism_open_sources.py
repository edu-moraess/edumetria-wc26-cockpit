"""
etl/extractors/tourism_open_sources.py
Extractor de turismo com fallback para placeholders.
"""

import sys
from pathlib import Path
from datetime import date, datetime
import requests
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR
from config_secrets import get_secret

def fetch_statcan_tourism() -> pd.DataFrame:
    """Tenta baixar dados reais da StatCan via CSV."""
    url = "https://www150.statcan.gc.ca/t1/tbl1/en/dtl!download"
    params = {"pid": "24100041", "format": "csv", "lang": "eng"}
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        df = pd.read_csv(pd.compat.StringIO(resp.text), skiprows=1, low_memory=False)
        # Procura a coluna que contém a categoria de viajantes
        cat_col = None
        for col in df.columns:
            if 'category' in col.lower():
                cat_col = col
                break
        if cat_col is None:
            cat_col = df.columns[2]  # fallback
        # Busca 'Total' na categoria
        mask = (df[cat_col].str.contains('Total', na=False, case=False)) & (df['UOM'] == 'Number')
        subset = df.loc[mask, ['REF_DATE', 'VALUE']].copy()
        subset = subset.dropna(subset=['VALUE'])
        subset['date'] = pd.to_datetime(subset['REF_DATE'], format='%Y-%m', errors='coerce')
        subset = subset.dropna(subset=['date'])
        subset = subset.rename(columns={'VALUE': 'value'})
        return subset[['date', 'value']]
    except Exception as e:
        print(f"  Erro StatCan: {e}")
        return pd.DataFrame()

def fetch_banxico(series_id, token):
    url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{series_id}/datos"
    headers = {"Bmx-Token": token}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        obs = data["bmx"]["series"][0]["datos"]
        df = pd.DataFrame(obs)
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
        df["value"] = pd.to_numeric(df["value"].astype(str).str.replace(",", ""), errors="coerce")
        return df.dropna()
    except Exception as e:
        print(f"  Erro Banxico: {e}")
        return pd.DataFrame()

def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    # --- Canadá ---
    print("Baixando turismo Canadá...")
    df_can = fetch_statcan_tourism()
    if df_can.empty:
        print("  Dados reais não obtidos. Criando placeholder para Canadá.")
        dates = pd.date_range(start="2010-01-01", end=date.today(), freq='MS')
        df_can = pd.DataFrame({"date": dates, "value": 1_000_000})
    else:
        print(f"  Dados reais: {len(df_can)} registros, último {df_can['date'].max().date()}")
    df_can["country"] = "CAN"
    df_can["indicator_label"] = "chegadas_internacionais_canada_total"
    frames.append(df_can)

    # --- México ---
    token = get_secret("BANXICO_TOKEN")
    if token:
        print("Baixando turismo México...")
        df_mex = fetch_banxico("SE39037", token)
        if df_mex.empty:
            print("  Placeholder para México")
            dates = pd.date_range(start="2010-01-01", end=date.today(), freq='MS')
            df_mex = pd.DataFrame({"date": dates, "value": 500_000})
        else:
            print(f"  Dados reais: {len(df_mex)} registros, último {df_mex['date'].max().date()}")
    else:
        print("  Token Banxico não definido. Criando placeholder para México.")
        dates = pd.date_range(start="2010-01-01", end=date.today(), freq='MS')
        df_mex = pd.DataFrame({"date": dates, "value": 500_000})

    df_mex["country"] = "MEX"
    df_mex["indicator_label"] = "turistas_internacionais_mexico"
    frames.append(df_mex)

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"tourism_open_sources_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} ({len(result):,} linhas)")
    return result

if __name__ == "__main__":
    run()