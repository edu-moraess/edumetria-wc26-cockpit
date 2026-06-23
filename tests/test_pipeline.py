"""
Testes de integridade do pipeline ETL.
"""
import pytest
import sys
import os

# Adicionar raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from etl.extractors import fred, yfinance_markets, tourism_open_sources
from etl.transformers import clean_macro, clean_markets, clean_tourism


class TestExtractors:
    """Testa extractors com dados mock quando APIs não disponíveis."""
    
    def test_fred_extractor_structure(self, monkeypatch):
        """FRED extractor retorna DataFrame com colunas esperadas."""
        import pandas as pd
        mock_df = pd.DataFrame({
            "date": pd.date_range("2020-01-01", periods=10, freq="QS"),
            "GDP": range(10)
        }).set_index("date")
        
        monkeypatch.setattr(fred, "get_series", lambda key: mock_df)
        
        result = fred.fetch_macro_series("GDP")
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
    
    def test_yfinance_extractor_valid_tickers(self):
        """Tickers principais devem ser válidos."""
        tickers = yfinance_markets.TICKERS_MAIN
        assert len(tickers) > 0
        assert all(isinstance(t, str) for t in tickers)
        assert "^GSPC" in tickers


class TestTransformers:
    """Testa lógica de transformação."""
    
    def test_yield_spread_calculation(self):
        """Yield spread 10Y-2Y calculado corretamente."""
        import pandas as pd
        df = pd.DataFrame({
            "date": pd.date_range("2020-01-01", periods=5, freq="M"),
            "DGS10": [2.0, 2.1, 2.2, 2.3, 2.4],
            "DGS2": [0.5, 0.6, 0.7, 0.8, 0.9]
        }).set_index("date")
        
        result = clean_macro.calculate_yield_spread(df, "DGS10", "DGS2")
        expected = [1.5, 1.5, 1.5, 1.5, 1.5]
        assert list(result["YIELD_SPREAD_10Y_2Y"]) == expected
    
    def test_tourism_tidy_format(self):
        """Dados de turismo em formato tidy (long)."""
        import pandas as pd
        df = pd.DataFrame({
            "date": ["2020-01", "2020-01"],
            "country": ["CAN", "MEX"],
            "arrivals": [1000, 2000]
        })
        
        result = clean_tourism.to_tidy(df)
        assert "indicator" in result.columns
        assert "value" in result.columns
