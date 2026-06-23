"""
models/montecarlo/wcli_calculator.py
World Cup Legacy Index (WCLI) — cálculo proprietário de legado.
VERSÃO v4: Integra FDI (World Bank), PIB (DiD), Emprego (FRED), Infraestrutura (proxy)

WCLI = 0.25*PIB + 0.20*Emprego + 0.20*Turismo + 0.15*FDI + 0.10*Infra + 0.10*ESG

Cada componente é normalizado em escala 0-100 antes de ponderar.
Componentes sem dados/modelo ainda retornam None e são excluídos do
cálculo (com peso redistribuído proporcionalmente).

Uso:
    python -m models.montecarlo.wcli_calculator
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import WCLI_WEIGHTS, WCLI_CLASSIFICATION, HOST_COUNTRIES  # noqa: E402
from database.connection import get_connection  # noqa: E402


def classify_wcli(score: float) -> str:
    for low, high, label in WCLI_CLASSIFICATION:
        if low <= score < high:
            return label
    return WCLI_CLASSIFICATION[-1][2]


def score_turismo(country_code: str) -> float | None:
    """
    Score de turismo (0-100): variação % das chegadas internacionais no
    último ano disponível vs. ano anterior, normalizada.
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
        score = (pct_change + 20) / 40 * 100
        return max(0.0, min(100.0, score))


def score_pib(country_code: str) -> float | None:
    """
    Score de PIB (0-100): crescimento real do PIB via World Bank ou FRED.
    Heurística: crescimento 0% -> 50, +4% -> 100, -4% -> 0.
    """
    with get_connection() as conn:
        # Tenta World Bank primeiro
        df = conn.execute(
            """
            SELECT period, value
            FROM fact_indicator_values
            WHERE country_code = ? AND indicator_code = 'WB_GDP_GROWTH'
            ORDER BY period
            """,
            [country_code],
        ).df()
        
        # Fallback para FRED GDP_REAL
        if df.empty:
            df = conn.execute(
                """
                SELECT period, value
                FROM fact_indicator_values
                WHERE country_code = ? AND indicator_code = 'GDP_REAL'
                ORDER BY period
                """,
                [country_code],
            ).df()
            if not df.empty and len(df) >= 2:
                df["period"] = pd.to_datetime(df["period"])
                df = df.set_index("period")["value"].resample("YE").last()
                if len(df) >= 2:
                    last, prev = df.iloc[-1], df.iloc[-2]
                    growth = (last / prev - 1) * 100
                    score = (growth + 4) / 8 * 100
                    return max(0.0, min(100.0, score))
            return None
        
        if not df.empty:
            last = df.iloc[-1]["value"]
            score = (last + 4) / 8 * 100
            return max(0.0, min(100.0, score))
        
        return None


def score_emprego(country_code: str) -> float | None:
    """
    Score de emprego (0-100): taxa de desemprego invertida.
    Menor desemprego = maior score. 3% -> 100, 10% -> 0.
    """
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value
            FROM fact_indicator_values
            WHERE country_code = ? AND indicator_code = 'UNEMPLOYMENT_RATE'
            ORDER BY period
            """,
            [country_code],
        ).df()
        
        if df.empty:
            return None
        
        last = df.iloc[-1]["value"]
        score = (10 - last) / 7 * 100
        return max(0.0, min(100.0, score))


def score_fdi(country_code: str) -> float | None:
    """
    Score de FDI (0-100): inflows de FDI via World Bank.
    Heurística: baseado em variação YoY do FDI.
    """
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value
            FROM fact_indicator_values
            WHERE country_code = ? AND indicator_code = 'WB_FDI_INFLOWS'
            ORDER BY period
            """,
            [country_code],
        ).df()
        
        if df.empty or len(df) < 2:
            return None
        
        df["period"] = pd.to_datetime(df["period"])
        df = df.set_index("period")["value"].resample("YE").sum()
        
        if len(df) < 2:
            return None
        
        last, prev = df.iloc[-1], df.iloc[-2]
        if prev == 0 or prev < 0:
            return 50.0
        
        pct_change = (last / prev - 1) * 100
        score = (pct_change + 20) / 40 * 100
        return max(0.0, min(100.0, score))


def score_infraestrutura(country_code: str) -> float | None:
    """
    Score de infraestrutura (0-100): proxy via construção civil / investimento em infra.
    Usa variação do índice de construção ou proxy com dados disponíveis.
    """
    with get_connection() as conn:
        # Tenta usar dados de construção civil (se disponível)
        df = conn.execute(
            """
            SELECT period, value
            FROM fact_indicator_values
            WHERE country_code = ? AND indicator_code LIKE '%CONSTRUCTION%'
            ORDER BY period
            """,
            [country_code],
        ).df()
        
        if not df.empty and len(df) >= 2:
            last = df.iloc[-1]["value"]
            prev = df.iloc[-2]["value"]
            if prev > 0:
                pct_change = (last / prev - 1) * 100
                score = (pct_change + 10) / 20 * 100
                return max(0.0, min(100.0, score))
        
        # Fallback: proxy com PIB e turismo (infraestrutura correlacionada)
        pib_score = score_pib(country_code)
        turismo_score = score_turismo(country_code)
        if pib_score is not None and turismo_score is not None:
            return (pib_score * 0.6 + turismo_score * 0.4)
        
        return None


def score_esg(country_code: str) -> float | None:
    """
    Score ESG (0-100): placeholder — requer dados de emissões/compensação de carbono.
    Fallback: proxy com eficiência energética (preço de energia invertido).
    """
    with get_connection() as conn:
        df = conn.execute(
            """
            SELECT period, value
            FROM fact_indicator_values
            WHERE country_code = ? AND indicator_code IN ('WTI_CRUDE', 'BRENT_CRUDE', 'NATURAL_GAS')
            ORDER BY period DESC
            LIMIT 1
            """,
            [country_code],
        ).df()
        
        if df.empty:
            return None
        
        # Preço de energia baixo = melhor ESG (proxy simplificado)
        last_price = df.iloc[0]["value"]
        score = (150 - last_price) / 130 * 100
        return max(0.0, min(100.0, score))


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
    print("World Cup Legacy Index (WCLI) — cálculo v4\n")
    for country_code in HOST_COUNTRIES:
        result = calculate_wcli(country_code)
        print(f"--- {country_code} ---")
        for comp, score in result["scores"].items():
            status = f"{score:.1f}" if score is not None else "pendente"
            print(f" {comp:15s}: {status}")

        if result["wcli_total"] is not None:
            print(f" WCLI total : {result['wcli_total']:.1f} ({result['classification']})")
        else:
            print(" WCLI total : indisponível (nenhum componente calculável)")

        print(f" Completeness : {result['completeness_pct']:.0f}% do índice baseado em dados reais\n")


if __name__ == "__main__":
    run()
