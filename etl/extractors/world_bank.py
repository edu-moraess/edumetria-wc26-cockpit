"""
etl/extractors/world_bank.py
Extractor de dados históricos via World Bank API (gratuita, sem token).

OBJETIVO:
- Dados históricos das Copas anteriores (2006, 2010, 2014, 2018, 2022)
  para comparação no Event Study
- Indicadores macroeconômicos anuais para os 3 países-sede e controles
- Base para o modelo DiD/Synthetic Control (fase pós-MVP)

ATIVAR: sem configuração adicional necessária — API pública.
Adicionar ao run_pipeline.py quando pronto para integrar.

REFERÊNCIA: https://datahelpdesk.worldbank.org/knowledgebase/articles/898581
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

WB_BASE_URL = "https://api.worldbank.org/v2"

# Países host + controles para DiD (similaridade econômica)
HOST_COUNTRIES    = ["USA", "CAN", "MEX"]
CONTROL_COUNTRIES = ["GBR", "AUS", "ESP", "FRA", "DEU", "BRA", "ARG", "KOR"]
ALL_COUNTRIES     = HOST_COUNTRIES + CONTROL_COUNTRIES

# Indicadores World Bank relevantes para o estudo
WB_INDICATORS = {
    "NY.GDP.MKTP.CD":       "gdp_current_usd",
    "NY.GDP.MKTP.KD.ZG":    "gdp_growth_pct",
    "SP.POP.TOTL":          "population",
    "FP.CPI.TOTL.ZG":       "inflation_cpi",
    "SL.UEM.TOTL.ZS":       "unemployment_rate",
    "BX.KLT.DINV.CD.WD":    "fdi_inflows_usd",
    "ST.INT.ARVL":           "international_tourist_arrivals",
    "ST.INT.RCPT.CD":        "tourism_receipts_usd",
    "NE.TRD.GNFS.ZS":       "trade_pct_gdp",
    "GC.DOD.TOTL.GD.ZS":    "govt_debt_pct_gdp",
}

START_YEAR = 2000
END_YEAR   = 2024


def fetch_wb_indicator(indicator: str, countries: list[str]) -> pd.DataFrame:
    """
    Busca um indicador do World Bank para múltiplos países.
    Retorna DataFrame tidy (country, year, value).
    """
    country_str = ";".join(countries)
    url = f"{WB_BASE_URL}/country/{country_str}/indicator/{indicator}"
    params = {
        "format":    "json",
        "per_page":  1000,
        "mrv":       END_YEAR - START_YEAR + 1,
        "date":      f"{START_YEAR}:{END_YEAR}",
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if len(data) < 2 or not data[1]:
        return pd.DataFrame()

    rows = []
    for item in data[1]:
        if item.get("value") is None:
            continue
        rows.append({
            "country_code": item["country"]["id"],
            "country_name": item["country"]["value"],
            "year":         int(item["date"]),
            "value":        float(item["value"]),
        })

    return pd.DataFrame(rows)


def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today  = date.today().isoformat()
    frames = []

    for indicator, label in WB_INDICATORS.items():
        print(f"Baixando World Bank {indicator} ({label})...")
        try:
            df = fetch_wb_indicator(indicator, ALL_COUNTRIES)
            if df.empty:
                print(f"  ⚠️  Sem dados para {indicator}")
                continue
            df["indicator_label"] = label
            df["indicator_code"]  = indicator
            frames.append(df)
            print(f"  → {len(df)} observações ({df['country_code'].nunique()} países)")
        except Exception as e:
            print(f"  ⚠️  Erro {indicator}: {e}")

    if not frames:
        print("Nenhum dado extraído do World Bank.")
        return None

    result   = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"world_bank_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\nSalvo: {out_path} ({len(result):,} linhas)")
    return result


if __name__ == "__main__":
    run()