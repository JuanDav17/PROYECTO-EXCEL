# backend/models.py
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

# Base declarativa que usarán todos los modelos
Base = declarative_base()

class Contacto(Base):
    """
    Modelo final para la persistencia de datos validados.
    Coincide con las columnas esperadas en el Excel.
    """
    __tablename__ = "contactos"
    
    # Llave Primaria (PK). Usamos String para IDs alfanuméricos.
    id = Column(String(100), primary_key=True, index=True)
    nombre = Column(String(255), index=True)
    direccion = Column(String(500))
    telefono = Column(String(100))
    correo = Column(String(255), index=True)

class ExcelRow(Base):
    """
    Modelo Antiguo / Universal. 
    Se mantiene por compatibilidad, pero la nueva lógica usa 'Contacto'.
    """
    __tablename__ = "excel_data_universal"
    id = Column(Integer, primary_key=True, index=True)
    row_content_json = Column(Text)