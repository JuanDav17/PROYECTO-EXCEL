# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importamos Base desde models.py para que los modelos sean accesibles
from models import Base 

# --- CONFIGURACIÓN DE CONEXIÓN (Variables de Entorno) ---
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASS = os.getenv("MYSQL_PASSWORD", "root")
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("MYSQL_DATABASE", "fastapi_db")
DB_PORT = os.getenv("DB_PORT", "3306")

# URL de conexión (usa pymysql como driver)
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# Motor de la base de datos
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# Sesión Local (para las dependencias de FastAPI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependencia de FastAPI para obtener una sesión de base de datos.
    Asegura que la sesión se cierre después de cada solicitud.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
