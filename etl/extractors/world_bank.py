"""
etl/extractors/world_bank.py
Extractor de dados macro do World Bank (dados históricos para DiD/Synthetic Control).

VERSÃO v4: Integrado no pipeline, formato tidy, dados para inferência causal.

Séries extraídas:
- NY.GDP.MKTP.KD.ZG: Crescimento do PIB (%)
- BX.KLT.DINV.CD.WD: FDI Inflows (US$)
- ST.INT.ARVL: Chegadas turísticas internacionais
- ST.INT.RCPT.CD: Receita turística (US$)
"""

import sys
from pathlib import Path
from datetime import date

import pandas as pd
import wbgapi as wb

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RAW_DATA_DIR  # noqa: E402

# Códigos do World Bank
WB_SERIES = {
    "NY.GDP.MKTP.KD.ZG": "GDP_GROWTH",
    "BX.KLT.DINV.CD.WD": "FDI_INFLOWS",
    "ST.INT.ARVL": "TOURIST_ARRIVALS",
    "ST.INT.RCPT.CD": "TOURISM_RECEIPTS",
}

# Países de interesse (ISO3)
WB_COUNTRIES = [
    "USA", "CAN", "MEX",  # Sede 2026
    "BRA", "ZAF", "RUS", "QAT", "DEU",  # Copas anteriores (para DiD)
    "ARG", "CHL", "COL", "PER", "FRA", "ESP", "GBR", "AUS",  # Controles
]


def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    
    print(f"Baixando dados do World Bank ({len(WB_SERIES)} séries × {len(WB_COUNTRIES)} países)...")
    
    frames = []
    for wb_code, label in WB_SERIES.items():
        try:
            df = wb.data.DataFrame(wb_code, WB_COUNTRIES, time=range(2000, 2026), numericTimeKeys=True, labels=False)
            if df.empty:
                print(f" ⚠️ {label}: sem dados")
                continue
            
            # Reset index para formato tidy
            df = df.reset_index()
            df = df.melt(id_vars=["economy"], var_name="year", value_name="value")
            df = df.dropna(subset=["value"])
            
            df["indicator_label"] = label
            df["indicator_code"] = f"WB_{label}"
            df["country_code"] = df["economy"]
            df["date"] = pd.to_datetime(df["year"].astype(str) + "-12-31")
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.dropna(subset=["value"])
            
            frames.append(df[["country_code", "indicator_code", "indicator_label", "date", "value"]])
            print(f" ✓ {label}: {len(df)} observações")
            
        except Exception as e:
            print(f" ⚠️ {label}: erro — {e}")
    
    if not frames:
        print("✗ Nenhum dado do World Bank obtido")
        return None
    
    result = pd.concat(frames, ignore_index=True)
    out_path = RAW_DATA_DIR / f"world_bank_{today}.csv"
    result.to_csv(out_path, index=False)
    print(f"\n✓ Salvo: {out_path} ({len(result):,} linhas, {result['country_code'].nunique()} países)")
    return result


if __name__ == "__main__":
    run()
