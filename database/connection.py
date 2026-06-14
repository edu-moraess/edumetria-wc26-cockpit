"""
database/connection.py
Gerencia conexão com DuckDB/Postgres e inicializa o esquema sem dropar tabelas.
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import duckdb
import psycopg2
from config import DB_BACKEND, DUCKDB_PATH, DATABASE_DIR

def get_connection():
    """Retorna conexão com o banco conforme configuração."""
    if DB_BACKEND == 'duckdb':
        return duckdb.connect(DUCKDB_PATH)
    elif DB_BACKEND == 'postgres':
        return psycopg2.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB")
        )
    else:
        raise ValueError(f"Backend desconhecido: {DB_BACKEND}")

def init_schema():
    """
    Cria as tabelas necessárias se elas não existirem.
    NUNCA droppa tabelas existentes (preserva dependências como chaves estrangeiras).
    """
    conn = get_connection()
    
    # SQL para criação segura (IF NOT EXISTS)
    create_script = """
    -- Tabelas de dimensão
    CREATE TABLE IF NOT EXISTS dim_indicator (
        indicator_code TEXT PRIMARY KEY,
        name TEXT,
        unit TEXT,
        category TEXT
    );

    CREATE TABLE IF NOT EXISTS dim_source (
        source_id INTEGER PRIMARY KEY,
        source_name TEXT,
        type TEXT,
        tier TEXT
    );

    -- Tabela fato principal (indicadores)
    CREATE TABLE IF NOT EXISTS fact_indicator_values (
        id INTEGER PRIMARY KEY,
        country_code TEXT,
        city_id TEXT,
        indicator_code TEXT,
        scenario_code TEXT,
        source_id INTEGER,
        period DATE,
        period_type TEXT,
        value REAL,
        is_forecast BOOLEAN,
        confidence_low REAL,
        confidence_high REAL,
        version INTEGER,
        FOREIGN KEY (indicator_code) REFERENCES dim_indicator(indicator_code),
        FOREIGN KEY (source_id) REFERENCES dim_source(source_id)
    );

    -- Tabela de distribuições Monte Carlo (depende de fact_indicator_values)
    CREATE TABLE IF NOT EXISTS fact_montecarlo_distribution (
        simulation_id INTEGER,
        indicator_code TEXT,
        period DATE,
        percentile_10 REAL,
        percentile_25 REAL,
        percentile_50 REAL,
        percentile_75 REAL,
        percentile_90 REAL,
        FOREIGN KEY (indicator_code) REFERENCES dim_indicator(indicator_code)
    );

    -- Outras tabelas fact_* que você possa ter (adicione se necessário)
    CREATE TABLE IF NOT EXISTS fact_forecast (
        id INTEGER PRIMARY KEY,
        indicator_code TEXT,
        period DATE,
        value REAL,
        scenario_code TEXT,
        version INTEGER
    );
    """

    if DB_BACKEND == 'duckdb':
        conn.execute(create_script)
        print("Esquema criado/verificado no DuckDB (sem DROPs).")
    elif DB_BACKEND == 'postgres':
        with conn.cursor() as cur:
            cur.execute(create_script)
        conn.commit()
        print("Esquema criado/verificado no Postgres (sem DROPs).")
    
    conn.close()

# Alias para compatibilidade
init_db = init_schema

if __name__ == "__main__":
    init_schema()