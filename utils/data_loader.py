"""
utils/data_loader.py
Data Loader centralizado e cacheado para todas as páginas do dashboard.
"""
import streamlit as st
import pandas as pd
from database.connection import get_connection


@st.cache_data(ttl=300, show_spinner=False)
def load_indicator(indicator_code: str, country_code: str | None = None) -> pd.DataFrame:
    try:
        with get_connection() as conn:
            if country_code:
                df = conn.execute(
                    """
                    SELECT period, value 
                    FROM fact_indicator_values
                    WHERE indicator_code = ? AND country_code = ?
                    ORDER BY period
                    """,
                    [indicator_code, country_code],
                ).df()
            else:
                df = conn.execute(
                    """
                    SELECT period, value 
                    FROM fact_indicator_values
                    WHERE indicator_code = ?
                    ORDER BY period
                    """,
                    [indicator_code],
                ).df()
        
        if df.empty:
            return pd.DataFrame(columns=["period", "value"])
        
        df["period"] = pd.to_datetime(df["period"])
        return df
    
    except Exception:
        return pd.DataFrame(columns=["period", "value"])


@st.cache_data(ttl=300, show_spinner=False)
def load_latest_value(indicator_code: str, country_code: str | None = None) -> float | None:
    df = load_indicator(indicator_code, country_code)
    if df.empty:
        return None
    return float(df.iloc[-1]["value"])


@st.cache_data(ttl=300, show_spinner=False)
def load_multiple_indicators(indicators: list[tuple[str, str | None]]) -> dict:
    results = {}
    for code, country in indicators:
        key = f"{code}_{country}" if country else code
        results[key] = load_indicator(code, country)
    return results


@st.cache_data(ttl=300, show_spinner=False)
def get_data_summary() -> dict:
    try:
        with get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) AS n FROM fact_indicator_values").df()["n"][0]
            indicators = conn.execute(
                "SELECT DISTINCT indicator_code FROM fact_indicator_values"
            ).df()["indicator_code"].tolist()
            countries = conn.execute(
                "SELECT DISTINCT country_code FROM fact_indicator_values WHERE country_code IS NOT NULL"
            ).df()["country_code"].tolist()
            latest = conn.execute(
                "SELECT MAX(period) as last_date FROM fact_indicator_values"
            ).df()["last_date"][0]
        
        return {
            "total_records": int(total),
            "n_indicators": len(indicators),
            "n_countries": len(countries),
            "latest_date": pd.to_datetime(latest).strftime("%Y-%m-%d") if latest else None,
            "indicators": indicators,
            "countries": countries,
        }
    except Exception:
        return {"total_records": 0, "n_indicators": 0, "n_countries": 0, "latest_date": None}
