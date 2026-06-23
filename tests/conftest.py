"""
Configurações globais de teste.
"""
import pytest


def pytest_configure(config):
    """Registra marcadores customizados."""
    config.addinivalue_line("markers", "slow: marca testes lentos (requer API)")
    config.addinivalue_line("markers", "integration: marca testes de integração")


@pytest.fixture(scope="session")
def test_data_dir():
    """Diretório de dados de teste."""
    import os
    return os.path.join(os.path.dirname(__file__), "fixtures")
 