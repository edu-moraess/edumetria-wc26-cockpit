"""
models/montecarlo/wcli_calculator.py
World Cup Legacy Index (WCLI) — cálculo proprietário de legado.

WCLI = 0.25*PIB + 0.20*Emprego + 0.20*Turismo + 0.15*FDI + 0.10*Infra + 0.10*ESG

Cada componente é normalizado em escala 0-100 antes de ponderar.
Componentes sem dados/modelo ainda retornam None e são excluídos do
cálculo (com peso redistribuído proporcionalmente) — o resultado vem
acompanhado de um "completeness score" indicando quanto do índice é
baseado em dados reais vs. pendente.

Uso:
    python -m models.montecarlo.wcli_calculator
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import WCLI_WEIGHTS, WCLI_CLASSIFICATION, HOST_COUNTRIES  # noqa: E402
from database.connection import get_connection  # noqa: E402


def classify_wcli(score: float) -> str:
    for low, high, label in WCLI_CLASSIFICATION:
        if low <= score < high:
            return label
    return WCLI_CLASSIFICATION[-1][2]  # >= 80 cai em "Transformacional"


def score_turismo(country_code: str) -> float | None:
    """
    Score de turismo (0-100): variação % das chegadas internacionais no
    último ano disponível vs. ano anterior, normalizada.
    Heurística simples até a modelagem de impacto incremental existir:
    crescimento de 0% -> score 50; +20% -> score 100; -20% -> score 0.
    """
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value
            FROM fact_indicator_values
            WHERE country_code = ? AND indicator_code = 'TOURISM_ARRIVALS'
            ORDER BY period
            """,
            [country_code],
        ).df()

    if df.empty or len(df) < 13:
        return None

    df["period"] = pd.to_datetime(df["period"])
    df = df.set_index("period")["value"].resample("YE").sum()

    if len(df) < 2:
        return None

    last, prev = df.iloc[-1], df.iloc[-2]
    if prev == 0:
        return None

    pct_change = (last / prev - 1) * 100
    # mapeia [-20%, +20%] -> [0, 100], clip nas pontas
    score = (pct_change + 20) / 40 * 100
    return max(0.0, min(100.0, score))


def score_pib(country_code: str) -> float | None:
    """
    Placeholder: requer modelagem de impacto líquido (bruto - contrafactual).
    Retorna None até models/econometric/net_impact.py existir.
    """
    return None


def score_emprego(country_code: str) -> float | None:
    """Placeholder: requer modelagem de empregos incrementais."""
    return None


def score_fdi(country_code: str) -> float | None:
    """Placeholder: requer projeção de FDI 2026-2035."""
    return None


def score_infraestrutura(country_code: str) -> float | None:
    """Placeholder: requer avaliação de legado de infraestrutura (página Hotelaria/Urbano)."""
    return None


def score_esg(country_code: str) -> float | None:
    """Placeholder: requer dados de emissões/compensação de carbono."""
    return None


COMPONENT_FUNCS = {
    "pib": score_pib,
    "emprego": score_emprego,
    "turismo": score_turismo,
    "fdi": score_fdi,
    "infraestrutura": score_infraestrutura,
    "esg": score_esg,
}


def calculate_wcli(country_code: str) -> dict:
    """
    Calcula o WCLI para um país, usando apenas componentes com dados
    disponíveis. Pesos dos componentes ausentes são redistribuídos
    proporcionalmente entre os disponíveis.

    Retorna dict com scores individuais, wcli_total, classificação e
    completeness (% do peso total baseado em dados reais).
    """
    scores = {}
    for component, func in COMPONENT_FUNCS.items():
        scores[component] = func(country_code)

    available = {k: v for k, v in scores.items() if v is not None}
    completeness = sum(WCLI_WEIGHTS[k] for k in available) if available else 0.0

    if not available:
        wcli_total = None
        classification = "Indisponível"
    else:
        # redistribui pesos proporcionalmente entre componentes disponíveis
        weight_sum = sum(WCLI_WEIGHTS[k] for k in available)
        wcli_total = sum(
            available[k] * (WCLI_WEIGHTS[k] / weight_sum) for k in available
        )
        classification = classify_wcli(wcli_total)

    return {
        "country_code": country_code,
        "scores": scores,
        "wcli_total": wcli_total,
        "classification": classification,
        "completeness_pct": completeness * 100,
    }


def run():
    print("World Cup Legacy Index (WCLI) — cálculo preliminar\n")
    for country_code in HOST_COUNTRIES:
        result = calculate_wcli(country_code)
        print(f"--- {country_code} ---")
        for comp, score in result["scores"].items():
            status = f"{score:.1f}" if score is not None else "pendente"
            print(f"  {comp:15s}: {status}")

        if result["wcli_total"] is not None:
            print(f"  WCLI total      : {result['wcli_total']:.1f} ({result['classification']})")
        else:
            print("  WCLI total      : indisponível (nenhum componente calculável)")

        print(f"  Completeness    : {result['completeness_pct']:.0f}% do índice baseado em dados reais\n")


if __name__ == "__main__":
    run()
