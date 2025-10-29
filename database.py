from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Carrega variáveis do arquivo .env
load_dotenv()

# --- Configuração do banco ---
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# URL de conexão para SQLAlchemy com PyMySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# Cria engine do SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)

# Sessão para operações no banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Base para definir os modelos
Base = declarative_base()

# --- Modelo de usuário ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    hash_senha = Column(String(100), nullable=False)

# Cria as tabelas no banco caso não existam
Base.metadata.create_all(engine)
