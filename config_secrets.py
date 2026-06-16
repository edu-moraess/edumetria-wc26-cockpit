"""
config_secrets.py
Helper para ler credenciais tanto de st.secrets (Streamlit Cloud)
quanto de variáveis de ambiente / .env (execução local).

Uso:
    from config_secrets import get_secret
    api_key = get_secret("FRED_API_KEY")
"""

import os


def get_secret(key: str, default: str | None = None) -> str | None:
    """Tenta st.secrets primeiro (Streamlit Cloud), depois os.getenv (local/.env)."""
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return os.getenv(key, default)

