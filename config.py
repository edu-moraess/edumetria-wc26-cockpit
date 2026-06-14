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
#
# Paleta inspirada em terminais Bloomberg/Refinitiv e relatórios de
# quant research de Goldman Sachs, Two Sigma, AQR:
# - Fundo quase preto (não puro — reduz fadiga visual)
# - Surface levemente azulado (profundidade)
# - Accent: azul elétrico frio (não dourado) — padrão quant research
# - Texto: branco frio, não amarelado
# - Grid: quase invisível (cinza muito escuro)
# - Série primária: azul cobalto (#4C8BF5 — Google Blue, legível em dark)
# - Série secundária: ciano frio (#00C8FF — Refinitiv style)
# - Série terciária: âmbar frio (#FFB300 — acento quente controlado)
# - Positivo: verde menta frio (#00D4AA)
# - Negativo: vermelho coral frio (#FF4560)
# - Banda de confiança: azul translúcido (rgba do accent)
# ------------------------------------------------------------------
THEME = {
    "background": "#0A0E1A",       # quase preto, toque azulado
    "surface": "#111827",          # surface cards — cinza azulado escuro
    "surface_alt": "#1A2235",      # surface alternativo (hover, expander)
    "border": "#1E2D45",           # borda sutil azul-escura
    "primary": "#4C8BF5",          # azul cobalto — série principal
    "accent": "#00C8FF",           # ciano frio — série secundária
    "accent_warm": "#FFB300",      # âmbar controlado — destaque/alerta
    "secondary": "#6B7A99",        # texto secundário — cinza azulado
    "text": "#E2E8F0",             # texto principal — branco frio
    "text_muted": "#4A5568",       # texto desabilitado
    "positive": "#00D4AA",         # verde menta frio
    "negative": "#FF4560",         # vermelho coral frio
    "neutral": "#4C8BF5",          # neutro = primary
    "warning": "#FFB300",          # alerta = accent_warm
    "grid": "#1A2235",             # grid quase invisível
    "font_family": "'IBM Plex Mono', 'Roboto Mono', 'Courier New', monospace",
    # fonte monospace — padrão em terminais quant (Bloomberg, QuantConnect)
}

# Paleta de séries múltiplas — ordem de uso em gráficos multi-linha
# Inspirada em paletas de quant research (sem cores quentes excessivas)
SERIES_PALETTE = [
    "#4C8BF5",   # azul cobalto (primary)
    "#00C8FF",   # ciano frio
    "#00D4AA",   # verde menta
    "#FFB300",   # âmbar
    "#A78BFA",   # roxo suave
    "#F472B6",   # rosa frio
    "#FF4560",   # vermelho coral
    "#94A3B8",   # cinza azulado
]

PLOTLY_BASE = {
    "template": "plotly_dark",
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