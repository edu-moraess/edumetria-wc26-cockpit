"""
config.py
Configuração central do FIFA 2026 Impact Analytics Platform (Edumetria WC26 Cockpit).
"""

from pathlib import Path
import os

# ------------------------------------------------------------------
# PATHS
# ------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent

DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

DATABASE_DIR = ROOT_DIR / "database"
DUCKDB_PATH = DATABASE_DIR / "fifa2026.duckdb"

# Criar diretórios essenciais se não existirem
for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR, DATABASE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# BANCO DE DADOS
# ------------------------------------------------------------------
POSTGRES_URL = os.getenv(
    "FIFA2026_POSTGRES_URL",
    "postgresql://user:password@localhost:5432/fifa2026",
)

DB_BACKEND = os.getenv("FIFA2026_DB_BACKEND", "duckdb")

# ------------------------------------------------------------------
# HORIZONTE TEMPORAL DO ESTUDO
# ------------------------------------------------------------------
BASE_YEAR = 2026
FORECAST_START_YEAR = 2027
FORECAST_END_YEAR = 2035

# ------------------------------------------------------------------
# PAÍSES-SEDE
# ------------------------------------------------------------------
HOST_COUNTRIES = ["USA", "CAN", "MEX"]

COUNTRY_NAMES = {
    "USA": "Estados Unidos",
    "CAN": "Canadá",
    "MEX": "México",
}

# ------------------------------------------------------------------
# INDICADORES FIFA — BASE DE DADOS OBRIGATÓRIA (PONTO DE PARTIDA)
# ------------------------------------------------------------------
FIFA_BASELINE = {
    "global": {
        "output_usd_bn": 80.1,
        "gdp_usd_bn": 40.9,
        "jobs_fte": 824_000,
        "visitors_total": 6_500_000,
        "sroi": 3.64,
        "social_benefits_usd_bn": 8.28,
    },
    "USA": {
        "spend_usd_bn": 11.1,
        "output_usd_bn": 30.5,
        "gdp_usd_bn": 17.2,
        "jobs": 185_000,
        "gov_revenue_usd_bn": 3.4,
    },
    "CAN": {
        "output_cad_bn": 3.8,
        "gdp_cad_bn": 2.0,
        "jobs": 24_100,
    },
    "MEX": {
        "impact_usd_bn_low": 3.0,
        "impact_mxn_bn_high": 200.0,
    },
}

# ------------------------------------------------------------------
# WORLD CUP LEGACY INDEX (WCLI)
# ------------------------------------------------------------------
WCLI_WEIGHTS = {
    "pib": 0.25,
    "emprego": 0.20,
    "turismo": 0.20,
    "fdi": 0.15,
    "infraestrutura": 0.10,
    "esg": 0.10,
}

WCLI_CLASSIFICATION = [
    (0, 20, "Muito Fraco"),
    (20, 40, "Fraco"),
    (40, 60, "Moderado"),
    (60, 80, "Forte"),
    (80, 100, "Transformacional"),
]

# ------------------------------------------------------------------
# MONTE CARLO
# ------------------------------------------------------------------
MONTE_CARLO_N_SIMULATIONS = 100_000
MONTE_CARLO_RANDOM_SEED = 42

# ------------------------------------------------------------------
# CENÁRIOS MACROECONÔMICOS
# ------------------------------------------------------------------
SCENARIOS = ["conservador", "base", "otimista", "estresse"]

# ------------------------------------------------------------------
# IDENTIDADE VISUAL — QUANT INSTITUTIONAL GRADE
# ------------------------------------------------------------------
THEME = {
    "background": "#FFFFFF",
    "surface": "#F8FAFC",
    "surface_alt": "#F1F5F9",
    "border": "#E2E8F0",
    "primary": "#4C8BF5",
    "accent": "#00C8FF",
    "accent_warm": "#FFB300",
    "secondary": "#64748B",
    "text": "#0F172A",
    "text_muted": "#94A3B8",
    "positive": "#00D4AA",
    "negative": "#FF4560",
    "neutral": "#4C8BF5",
    "warning": "#FFB300",
    "grid": "#F1F5F9",
    "font_family": "'IBM Plex Mono', 'Roboto Mono', 'Courier New', monospace",
}

SERIES_PALETTE = [
    "#4C8BF5",
    "#00C8FF",
    "#00D4AA",
    "#FFB300",
    "#A78BFA",
    "#F472B6",
    "#FF4560",
    "#94A3B8",
]

PLOTLY_BASE = {
    "template": "plotly_white",
    "paper_bgcolor": THEME["background"],
    "plot_bgcolor": THEME["surface"],
    "font": {
        "family": THEME["font_family"],
        "color": THEME["text"],
        "size": 12,
    },
}

# ------------------------------------------------------------------
# BRANDING
# ------------------------------------------------------------------
BRAND = {
    "author": "Eduardo Moraes",
    "org": "Edumetria",
    "role": "Quant Data Scientist & Economics Researcher",
    "report_title": "FIFA World Cup 2026™ — Impact Analytics Platform",
}