import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "A variável DATABASE_URL não foi configurada no .env"
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

def testar_conexao():
    """Testa a comunicação com o banco PostgreSQL."""
    with engine.connect() as conexao:
        resultado = conexao.execute(text("SELECT 1"))
        return resultado.scalar() 

def get_db():
    """"
    Disponibiliza uma sessão do banco para cada requisição.
    Fecha a sessão ao finalizar o uso.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()