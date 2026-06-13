"""
etl/extractors/tourism_open_sources.py
Extractor de dados de turismo via fontes públicas/gratuitas — substitui
o Tourism Economics (pago) para o MVP.

Fontes:
- StatCan (Canadá): API REST aberta, sem chave necessária
- Banxico (México): API REST, requer "token" gratuito
  (obter em: https://www.banxico.org.mx/SieAPIRest/service/v1/token)
- US NTTO: não tem API REST moderna — dados via download manual de
  arquivos (CSV/XLSX) do site oficial; este extractor deixa o caminho
  documentado para integração futura via download manual + data/external/

NOTA: Este extractor cobre Canadá e México programaticamente. Para EUA,
o caminho recomendado no curto prazo é baixar manualmente os relatórios
do NTTO (https://www.trade.gov/national-travel-tourism-office) e colocar
em data/external/ntto_usa/ — o transformer correspondente lerá esse CSV.
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

# ------------------------------------------------------------------
# CANADÁ — Statistics Canada (StatCan) API
# Tabela 24-10-0053-01: Chegadas de viajantes internacionais
# ------------------------------------------------------------------
STATCAN_BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods"

# Vetor de exemplo: total de chegadas internacionais ao Canadá (mensal)
# Para encontrar outros vetores: https://www150.statcan.gc.ca/n1/pub/71-607-x/71-607-x2018005-eng.htm
STATCAN_VECTORS = {
    "v1": "chegadas_internacionais_canada_total",
}


def fetch_statcan(vector_id: str, n_periods: int = 60) -> pd.DataFrame:
    """Busca os últimos N períodos de um vetor StatCan."""
    payload = [{"vectorId": vector_id.replace("v", ""), "latestN": n_periods}]
    resp = requests.post(STATCAN_BASE_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for item in data:
        if item.get("status") != "SUCCESS":
            continue
        for point in item["object"]["vectorDataPoint"]:
            rows.append({
                "date": point["refPer"],
                "value": point["value"],
            })
    return pd.DataFrame(rows)


# ------------------------------------------------------------------
# MÉXICO — Banxico SIE API
# Serie de exemplo: visitantes internacionais (turistas)
# Token gratuito: https://www.banxico.org.mx/SieAPIRest/service/v1/token
# ------------------------------------------------------------------
BANXICO_BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"

# Série exemplo: SE39037 = Llegada de turistas internacionales (total)
BANXICO_SERIES = {
    "SE39037": "turistas_internacionais_mexico",
}


def fetch_banxico(series_id: str, token: str) -> pd.DataFrame:
    """Busca série completa do Banxico SIE."""
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


# ------------------------------------------------------------------
# RUN
# ------------------------------------------------------------------
def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    frames = []

    # --- Canadá ---
    for vector_id, label in STATCAN_VECTORS.items():
        try:
            print(f"Baixando StatCan {vector_id} ({label})...")
            df = fetch_statcan(vector_id)
            df["country"] = "CAN"
            df["indicator_label"] = label
            frames.append(df)
        except Exception as e:
            print(f"  ⚠️  Erro StatCan {vector_id}: {e}")

    # --- México ---
    banxico_token = os.getenv("BANXICO_TOKEN")
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
        print("  ⚠️  BANXICO_TOKEN não definido — pulando México. "
              "Obtenha em https://www.banxico.org.mx/SieAPIRest/service/v1/token")

    # --- EUA ---
    print("  ℹ️  EUA (NTTO): sem API automática. "
          "Baixar manualmente e colocar em data/external/ntto_usa/")

    if not frames:
        print("Nenhum dado extraído.")
        return None

    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"tourism_open_sources_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} ({len(result)} linhas)")
    return result


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run()
