import os
import duckdb
import psycopg2
from config import DB_BACKEND, DUCKDB_PATH

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
    # Usando sys.path para garantir a importação do config na raiz
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    
    from config import DB_DIR, DB_BACKEND
    schema_path = DB_DIR / "schema.sql"
    
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
  
