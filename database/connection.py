import os
import sys
from pathlib import Path

# ------------------------------------------------------------------
# Garante que o diretório raiz do projeto esteja no sys.path
# antes de qualquer import interno
# ------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import duckdb
import psycopg2
from config import DB_BACKEND, DUCKDB_PATH, DATABASE_DIR


def get_connection():
    """
    Retorna a conexão com o banco de dados configurado no .env.
    DuckDB é ideal para dev/testes. Postgres para produção.
    """
    if DB_BACKEND == 'duckdb':
        conn = duckdb.connect(DUCKDB_PATH)
        return conn
    elif DB_BACKEND == 'postgres':
        conn = psycopg2.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB")
        )
        return conn
    else:
        raise ValueError(f"Backend de banco de dados desconhecido: {DB_BACKEND}")


def init_db():
    """
    Lê o schema.sql e inicializa as tabelas no banco de dados.
    """
    schema_path = DATABASE_DIR / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Arquivo schema.sql não encontrado em {schema_path}")

    with open(schema_path, 'r') as file:
        schema_sql = file.read()

    conn = get_connection()
    if DB_BACKEND == 'duckdb':
        conn.execute(schema_sql)
        print("Tabelas inicializadas no DuckDB com sucesso.")
    elif DB_BACKEND == 'postgres':
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        print("Tabelas inicializadas no Postgres com sucesso.")
    conn.close()


if __name__ == "__main__":
    init_db()
