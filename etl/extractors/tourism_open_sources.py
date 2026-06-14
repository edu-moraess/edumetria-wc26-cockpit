"""
etl/extractors/tourism_open_sources.py
Extractor de dados de turismo via fontes públicas gratuitas.

CORREÇÃO v3:
- Canadá: substituído vector API por cubes API (garante dados atualizados até 2024)
- México: Banxico mantido
"""

import sys
from pathlib import Path
from datetime import date
import requests
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR
from config_secrets import get_secret

# ------------------------------------------------------------------
# CANADÁ — StatCan cubes API (tabela 24-10-0041-01)
# Retorna todos os dados históricos, não apenas últimos N períodos
# ------------------------------------------------------------------
STATCAN_CUBE_URL = "https://www150.statcan.gc.ca/t1/tbl1/en/dtl!download"
# Parâmetros para baixar CSV diretamente (formato mais confiável)
STATCAN_DOWNLOAD_PARAMS = {
    "pid": "24100041",  # tabela 24-10-0041-01
    "format": "csv",
    "lang": "eng",
}

def fetch_statcan_tourism() -> pd.DataFrame:
    """Baixa o CSV completo da tabela e extrai a série de chegadas totais."""
    resp = requests.get(STATCAN_CUBE_URL, params=STATCAN_DOWNLOAD_PARAMS, timeout=30)
    resp.raise_for_status()
    lines = resp.text.splitlines()
    # Procura pela linha de cabeçalho e dados
    data_lines = [l for l in lines if not l.startswith('"') and not l.startswith('REF_DATE')]
    # O formato CSV da StatCan é complexo; usamos pandas diretamente na string
    from io import StringIO
    df = pd.read_csv(StringIO(resp.text), skiprows=1, low_memory=False)
    # Filtra a série desejada: "Total, all visitors" ou "Total, international visitors"
    # Ajuste conforme a estrutura atual da tabela (pode variar)
    mask = (df['Traveller category'] == 'Total, all travellers') & (df['UOM'] == 'Number')
    if mask.sum() == 0:
        # Fallback: tenta outra categoria
        mask = (df['Traveller category'].str.contains('Total', case=False, na=False)) & (df['UOM'] == 'Number')
    subset = df.loc[mask, ['REF_DATE', 'VALUE']].copy()
    subset = subset.dropna(subset=['VALUE'])
    subset['date'] = pd.to_datetime(subset['REF_DATE'], format='%Y-%m', errors='coerce')
    subset = subset.dropna(subset=['date'])
    subset = subset.rename(columns={'VALUE': 'value'})
    return subset[['date', 'value']]

def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    # --- Canadá ---
    print("Baixando StatCan (tabela 24-10-0041-01) — chegadas internacionais...")
    try:
        df_can = fetch_statcan_tourism()
        if not df_can.empty:
            df_can["country"] = "CAN"
            df_can["indicator_label"] = "chegadas_internacionais_canada_total"
            frames.append(df_can)
            print(f"  → {len(df_can)} observações (última data: {df_can['date'].max().date()})")
        else:
            print("  ⚠️ Nenhum dado encontrado para Canadá.")
    except Exception as e:
        print(f"  ⚠️ Erro ao baixar dados do Canadá: {e}")

    # --- México (Banxico) ---
    banxico_token = get_secret("BANXICO_TOKEN")
    if banxico_token:
        def fetch_banxico(series_id: str, token: str) -> pd.DataFrame:
            url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{series_id}/datos"
            headers = {"Bmx-Token": token}
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            obs = data["bmx"]["series"][0]["datos"]
            df = pd.DataFrame(obs)
            df.columns = ["date", "value"]
            df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
            df["value"] = pd.to_numeric(df["value"].astype(str).str.replace(",", ""), errors="coerce")
            return df.dropna()
        for series_id, label in [("SE39037", "turistas_internacionais_mexico")]:
            print(f"Baixando Banxico {series_id}...")
            try:
                df_mex = fetch_banxico(series_id, banxico_token)
                if not df_mex.empty:
                    df_mex["country"] = "MEX"
                    df_mex["indicator_label"] = label
                    frames.append(df_mex)
                    print(f"  → {len(df_mex)} observações")
            except Exception as e:
                print(f"  ⚠️ Erro Banxico: {e}")
    else:
        print("  ⚠️ BANXICO_TOKEN não definido — pulando México.")

    if not frames:
        print("Nenhum dado extraído.")
        return None

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"tourism_open_sources_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\nSalvo: {out_path} ({len(result):,} linhas)")
    return result

if __name__ == "__main__":
    run()