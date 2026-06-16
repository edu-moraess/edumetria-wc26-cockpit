"""
database/connection.py — v3
CORREÇÕES: init_schema robusto, fallback statement-by-statement
"""

import duckdb
import sqlalchemy
from contextlib import contextmanager
from pathlib import Path

from config import DUCKDB_PATH, POSTGRES_URL, DB_BACKEND, DATABASE_DIR


def _ensure_db_dir():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    if DB_BACKEND == "duckdb":
        _ensure_db_dir()
        conn = duckdb.connect(str(DUCKDB_PATH))
        try:
            yield conn
        finally:
            conn.close()
    elif DB_BACKEND == "postgres":
        engine = sqlalchemy.create_engine(POSTGRES_URL)
        conn   = engine.connect()
        try:
            yield conn
        finally:
            conn.close()
    else:
        raise ValueError(f"DB_BACKEND inválido: {DB_BACKEND!r}")


def init_schema():
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema não encontrado: {schema_path}")

    sql = schema_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        if DB_BACKEND == "duckdb":
            try:
                conn.execute(sql)
            except Exception:
                for stmt in sql.split(";"):
                    stmt = stmt.strip()
                    if stmt and not stmt.startswith("--"):
                        try:
                            conn.execute(stmt)
                        except Exception as e2:
                            if "already exists" not in str(e2).lower():
                                print(f"  ⚠️  Statement ignorado: {e2}")
        elif DB_BACKEND == "postgres":
            for stmt in sql.split(";"):
                stmt = stmt.strip()
                if stmt and not stmt.startswith("--"):
                    try:
                        conn.execute(sqlalchemy.text(stmt))
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            print(f"  ⚠️  Postgres statement ignorado: {e}")
            conn.commit()


if __name__ == "__main__":
    init_schema()
    print(f"Schema inicializado com sucesso (backend={DB_BACKEND})") 