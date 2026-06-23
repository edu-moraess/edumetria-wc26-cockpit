"""
Testes de qualidade de dados — validam integridade pós-ETL.
"""
import pytest
import pandas as pd
import os
from datetime import datetime, timedelta


# Fixtures comuns
@pytest.fixture
def processed_dir():
    return "data/processed"


@pytest.fixture
def raw_dir():
    return "data/raw"


class TestMacroDataQuality:
    """Valida dados macroeconômicos (FRED)."""
    
    @pytest.fixture
    def macro_df(self, processed_dir):
        path = os.path.join(processed_dir, "macro_usa.parquet")
        if not os.path.exists(path):
            pytest.skip("macro_usa.parquet não encontrado — rode o ETL primeiro")
        return pd.read_parquet(path)
    
    def test_no_nulls_in_core_series(self, macro_df):
        """PIB, CPI, desemprego e juros não devem ter nulos."""
        core_cols = ["GDP", "CPIAUCSL", "UNRATE", "FEDFUNDS"]
        for col in core_cols:
            if col in macro_df.columns:
                null_count = macro_df[col].isna().sum()
                assert null_count == 0, f"{col} tem {null_count} valores nulos"
    
    def test_date_range_coverage(self, macro_df):
        """Dados devem cobrir pelo menos 10 anos."""
        if "date" in macro_df.columns:
            date_col = "date"
        else:
            date_col = macro_df.index.name or macro_df.index
            
        if isinstance(macro_df.index, pd.DatetimeIndex):
            date_range = macro_df.index.max() - macro_df.index.min()
        else:
            date_range = pd.to_datetime(macro_df[date_col].max()) - pd.to_datetime(macro_df[date_col].min())
        
        assert date_range.days >= 365 * 10, f"Cobertura insuficiente: {date_range.days} dias"
    
    def test_yield_spread_calculation(self, macro_df):
        """Yield Spread 10Y-2Y deve estar dentro de faixa histórica."""
        if "YIELD_SPREAD_10Y_2Y" in macro_df.columns:
            spread = macro_df["YIELD_SPREAD_10Y_2Y"].dropna()
            assert spread.min() >= -5, f"Spread mínimo suspeito: {spread.min()}"
            assert spread.max() <= 5, f"Spread máximo suspeito: {spread.max()}"
    
    def test_no_future_dates(self, macro_df):
        """Não deve haver dados com datas futuras."""
        today = pd.Timestamp.now().normalize()
        if isinstance(macro_df.index, pd.DatetimeIndex):
            max_date = macro_df.index.max()
        else:
            max_date = pd.to_datetime(macro_df["date"].max())
        assert max_date <= today + timedelta(days=5), f"Data futura detectada: {max_date}"


class TestMarketDataQuality:
    """Valida dados de mercado (yfinance)."""
    
    @pytest.fixture
    def market_df(self, processed_dir):
        path = os.path.join(processed_dir, "markets.parquet")
        if not os.path.exists(path):
            pytest.skip("markets.parquet não encontrado")
        return pd.read_parquet(path)
    
    def test_price_positive(self, market_df):
        """Preços devem ser positivos."""
        price_cols = [c for c in market_df.columns if "Close" in c or "Adj Close" in c]
        for col in price_cols:
            neg = (market_df[col] < 0).sum()
            assert neg == 0, f"{col} tem {neg} preços negativos"
    
    def test_vix_range(self, market_df):
        """VIX deve estar entre 5 e 100 (faixa histórica)."""
        vix_cols = [c for c in market_df.columns if "VIX" in c.upper()]
        for col in vix_cols:
            if col in market_df.columns:
                assert market_df[col].min() >= 5, f"VIX mínimo suspeito: {market_df[col].min()}"
                assert market_df[col].max() <= 100, f"VIX máximo suspeito: {market_df[col].max()}"


class TestTourismDataQuality:
    """Valida dados de turismo (StatCan + Banxico)."""
    
    @pytest.fixture
    def tourism_df(self, processed_dir):
        path = os.path.join(processed_dir, "tourism.parquet")
        if not os.path.exists(path):
            pytest.skip("tourism.parquet não encontrado")
        return pd.read_parquet(path)
    
    def test_arrivals_positive(self, tourism_df):
        """Chegadas turísticas devem ser >= 0."""
        arrival_cols = [c for c in tourism_df.columns if "arrival" in c.lower() or "chegada" in c.lower()]
        for col in arrival_cols:
            neg = (tourism_df[col] < 0).sum()
            assert neg == 0, f"{col} tem {neg} valores negativos"
    
    def test_canada_mexico_coverage(self, tourism_df):
        """Deve haver dados para CAN e MEX."""
        country_cols = [c for c in tourism_df.columns if any(x in c.upper() for x in ["CAN", "MEX", "CA", "MX"])]
        assert len(country_cols) >= 2, "Dados insuficientes para CAN/MEX"


class TestPipelineIntegrity:
    """Valida estrutura do pipeline como um todo."""
    
    def test_all_processed_files_exist(self, processed_dir):
        """Todos os parquets esperados devem existir."""
        expected = ["macro_usa.parquet", "markets.parquet", "tourism.parquet"]
        for f in expected:
            path = os.path.join(processed_dir, f)
            assert os.path.exists(path), f"Arquivo esperado não encontrado: {f}"
    
    def test_no_duplicate_records(self, processed_dir):
        """Não deve haver duplicatas por (date, indicator)."""
        for f in os.listdir(processed_dir):
            if f.endswith(".parquet"):
                df = pd.read_parquet(os.path.join(processed_dir, f))
                if "date" in df.columns and "indicator" in df.columns:
                    dups = df.duplicated(subset=["date", "indicator"]).sum()
                    assert dups == 0, f"{f} tem {dups} duplicatas"
 