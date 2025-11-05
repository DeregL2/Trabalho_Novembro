from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# --- Carrega variáveis do arquivo .env ---
load_dotenv()

# --- Configurações do banco de dados ---
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# --- Monta a URL de conexão ---
# Exemplo: mysql+pymysql://root:senha@localhost/trabalho_faculdade
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# --- Criação da engine ---
# 'echo=True' mostra os comandos SQL no terminal (útil para debug)
engine = create_engine(DATABASE_URL, echo=True)

# --- Criação da sessão ---
# 'session' será usada para inserir, buscar e alterar dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# --- Base para os modelos ---
Base = declarative_base()


# --- Modelo da tabela de usuários ---
class Usuario(Base):
    """
    Modelo representando a tabela 'usuarios'.
    Guarda informações de login e senha (hash).
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    hash_senha = Column(String(100), nullable=False)
    twofa_ativo = Column(Integer, default=0)  # 0 = desativado, 1 = ativado


# --- Cria as tabelas no banco se não existirem ---
Base.metadata.create_all(engine)
