"""
config.py
Configuração central do FIFA 2026 Impact Analytics Platform.
"""

from pathlib import Path
import os
import sys

# Garante que o diretório raiz esteja no sys.path (funciona no Streamlit Cloud)
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ------------------------------------------------------------------
# PATHS
# ------------------------------------------------------------------
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

DATABASE_DIR = ROOT_DIR / "database"
DUCKDB_PATH = DATABASE_DIR / "fifa2026.duckdb"

# ⬇️ LINHA OBRIGATÓRIA para o erro DB_DIR
DB_DIR = DATABASE_DIR   # aponta para a pasta do banco

# ------------------------------------------------------------------
# BANCO DE DADOS
# ------------------------------------------------------------------
POSTGRES_URL = os.getenv("FIFA2026_POSTGRES_URL", "postgresql://user:password@localhost:5432/fifa2026")
DB_BACKEND = os.getenv("FIFA2026_DB_BACKEND", "duckdb")

# ------------------------------------------------------------------
# DEMAIS CONFIGURAÇÕES (mantenha as que você já tinha)
# ------------------------------------------------------------------
BASE_YEAR = 2026
FORECAST_START_YEAR = 2027
FORECAST_END_YEAR = 2035

HOST_COUNTRIES = ["USA", "CAN", "MEX"]
COUNTRY_NAMES = {"USA": "Estados Unidos", "CAN": "Canadá", "MEX": "México"}

FIFA_BASELINE = {
    "global": {"output_usd_bn": 80.1, "gdp_usd_bn": 40.9, "jobs_fte": 824000, "visitors_total": 6500000, "sroi": 3.64, "social_benefits_usd_bn": 8.28},
    "USA": {"spend_usd_bn": 11.1, "output_usd_bn": 30.5, "gdp_usd_bn": 17.2, "jobs": 185000, "gov_revenue_usd_bn": 3.4},
    "CAN": {"output_cad_bn": 3.8, "gdp_cad_bn": 2.0, "jobs": 24100},
    "MEX": {"impact_usd_bn_low": 3.0, "impact_mxn_bn_high": 200.0},
}

WCLI_WEIGHTS = {"pib": 0.25, "emprego": 0.20, "turismo": 0.20, "fdi": 0.15, "infraestrutura": 0.10, "esg": 0.10}
WCLI_CLASSIFICATION = [(0,20,"Muito Fraco"), (20,40,"Fraco"), (40,60,"Moderado"), (60,80,"Forte"), (80,100,"Transformacional")]

MONTE_CARLO_N_SIMULATIONS = 100_000
MONTE_CARLO_RANDOM_SEED = 42
SCENARIOS = ["conservador", "base", "otimista", "estresse"]

THEME = {
    "background": "#0E1117",
    "surface": "#161B22",
    "primary": "#C9A227",
    "secondary": "#8B96A5",
    "text": "#E6E6E6",
    "positive": "#3FB68B",
    "negative": "#E5534B",
    "neutral": "#5B7FA6",
    "grid": "#2A2F3A",
    "font_family": "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
}
PLOTLY_BASE = {"template": "plotly_dark", "paper_bgcolor": THEME["background"], "plot_bgcolor": THEME["surface"], "font": {"family": THEME["font_family"], "color": THEME["text"]}}
BRAND = {"author": "Eduardo Moraes", "org": "Edumetria", "role": "Quant Data Scientist & Economics Researcher", "report_title": "FIFA World Cup 2026™ — Impact Analytics Platform"}