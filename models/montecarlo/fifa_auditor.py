"""
models/montecarlo/fifa_auditor.py
FIFA Projection Auditor (simplificado) — compara o crescimento de
turismo OBSERVADO (StatCan/Banxico) com o crescimento IMPLÍCITO no
baseline FIFA, e classifica a projeção FIFA como subestimada, acurada
ou superestimada.

LIMITAÇÃO IMPORTANTE: o baseline FIFA fornece apenas o impacto total
esperado para 2026 (visitantes incrementais totais), não uma série
histórica de "projeção vs. tempo". Este módulo, portanto, faz uma
comparação estrutural simples:

  - Calcula a taxa de crescimento histórica média (CAGR) do turismo
    em cada país, baseada nos dados reais disponíveis.
  - Compara com a taxa de crescimento que SERIA NECESSÁRIA em 2026
    para o país atingir sua fração proporcional dos 6.5M de
    visitantes totais do baseline FIFA.
  - Classifica se a meta implícita da FIFA é: Conservadora, Plausível,
    Otimista ou Excessivamente Otimista, em relação ao histórico
    observado de cada país.

Esta é uma auditoria ESTRUTURAL preliminar — não substitui a auditoria
completa com dados ano-a-ano de visitantes da Copa, que exigiria séries
específicas de turismo relacionado ao evento (ainda não disponíveis).

Uso:
    python -m models.montecarlo.fifa_auditor
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import FIFA_BASELINE, HOST_COUNTRIES, COUNTRY_NAMES  # noqa: E402
from database.connection import get_connection  # noqa: E402


def _load_annual_tourism(country_code: str) -> pd.Series:
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value FROM fact_indicator_values
            WHERE indicator_code = 'TOURISM_ARRIVALS' AND country_code = ?
            ORDER BY period
            """,
            [country_code],
        ).df()

    if df.empty:
        return pd.Series(dtype=float)

    df["period"] = pd.to_datetime(df["period"])
    annual = df.set_index("period")["value"].resample("YE").sum()
    # remove anos incompletos (heurística: ano com valor muito menor que a mediana)
    if len(annual) > 1:
        median = annual.median()
        annual = annual[annual > median * 0.5]
    return annual


def historical_cagr(series: pd.Series) -> float | None:
    """Calcula a taxa de crescimento anual composta (CAGR) da série."""
    if len(series) < 2:
        return None
    n_years = len(series) - 1
    start, end = series.iloc[0], series.iloc[-1]
    if start <= 0 or n_years <= 0:
        return None
    return (end / start) ** (1 / n_years) - 1


def implied_fifa_target(country_code: str, latest_value: float) -> float | None:
    """
    Estima a taxa de crescimento implícita que o país precisaria atingir
    em 2026 para que sua "parcela" dos visitantes incrementais FIFA
    (6.5M globais, alocados proporcionalmente ao PIB do país no baseline)
    se concretize. Esta é uma heurística estrutural, não uma projeção
    oficial da FIFA por país.
    """
    global_visitors = FIFA_BASELINE["global"]["visitors_total"]

    # alocação proporcional simples baseada em participação no gasto total
    # (apenas EUA tem gasto explícito no baseline; CAN/MEX usam proxy de
    # participação igual aos demais por falta de dado granular)
    weights = {"USA": 0.6, "CAN": 0.2, "MEX": 0.2}  # heurística documentada
    country_share = weights.get(country_code, 1 / len(HOST_COUNTRIES))

    implied_incremental = global_visitors * country_share

    if latest_value <= 0:
        return None

    implied_growth = implied_incremental / latest_value
    return implied_growth


def classify_audit(historical_cagr_val: float | None, implied_growth: float | None) -> str:
    if historical_cagr_val is None or implied_growth is None:
        return "Dados insuficientes"

    ratio = implied_growth / max(historical_cagr_val, 1e-6)

    if ratio < 0.5:
        return "Conservadora"
    elif ratio < 1.5:
        return "Plausível"
    elif ratio < 3.0:
        return "Otimista"
    else:
        return "Excessivamente Otimista"


def audit_country(country_code: str) -> dict:
    series = _load_annual_tourism(country_code)

    if series.empty:
        return {
            "country_code": country_code,
            "historical_cagr": None,
            "implied_growth": None,
            "classification": "Sem dados",
            "n_years": 0,
        }

    cagr = historical_cagr(series)
    latest = series.iloc[-1]
    implied = implied_fifa_target(country_code, latest)
    classification = classify_audit(cagr, implied)

    return {
        "country_code": country_code,
        "historical_cagr": cagr,
        "implied_growth": implied,
        "classification": classification,
        "n_years": len(series),
        "latest_value": float(latest),
        "latest_year": series.index[-1].year,
    }


def run():
    print("FIFA Projection Auditor (simplificado) — estrutura de crescimento de turismo\n")
    print(
        "⚠️  Comparação estrutural: CAGR histórico observado vs. crescimento "
        "implícito necessário para a parcela do país no baseline global FIFA "
        "(6.5M visitantes incrementais). Alocação por país é heurística "
        "(EUA 60% / CAN 20% / MEX 20%) — não é uma projeção oficial FIFA por país.\n"
    )

    for country_code in HOST_COUNTRIES:
        result = audit_country(country_code)
        print(f"--- {COUNTRY_NAMES[country_code]} ---")
        if result["classification"] in ("Sem dados", "Dados insuficientes"):
            print(f"  {result['classification']}\n")
            continue

        print(f"  Anos observados        : {result['n_years']}")
        print(f"  Último ano             : {result['latest_year']}")
        print(f"  CAGR histórico         : {result['historical_cagr']*100:.1f}%")
        print(f"  Crescimento implícito  : {result['implied_growth']*100:.1f}% (para 2026)")
        print(f"  Classificação          : {result['classification']}\n")


if __name__ == "__main__":
    run()
