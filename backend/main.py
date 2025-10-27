# backend/main.py
# --- Importaciones de Sistema y Utilidades ---
import os
import io
import json
import sys
from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd

# --- Importaciones Locales (Necesarias) ---
# Asegurar path para imports locales
# Nota: La línea siguiente asume que estás ejecutando main.py desde un nivel superior.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importación de database y models (ASUMIMOS QUE EXISTEN Y ESTÁN CORRECTOS)
import database
from database import get_db, engine
from models import Base, Contacto, ExcelRow 

# --- CONFIGURACIÓN PRINCIPAL ---

# Definición de columnas esperadas (IMPORTANTE: deben coincidir con la tabla 'Contacto')
# Normalizadas a minúsculas, sin acentos (si la DB lo requiere) para validación robusta
# He normalizado 'dirección' a 'direccion' y 'teléfono' a 'telefono' para mayor compatibilidad.
EXPECTED_COLUMNS = ['id', 'nombre', 'direccion', 'telefono', 'correo']

app = FastAPI(title="Excel Uploader API v2")

# Crea las tablas (Contacto y ExcelRow) si no existen
Base.metadata.create_all(bind=engine)

# --------------------------
# Configuración CORS
# --------------------------
origins = [
    "http://localhost:8080", 
    "http://127.0.0.1:8080",
    "http://localhost:4200",  # Puerto default de Angular 
    "http://127.0.0.1:4200",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------

# Cola global WebSocket
websocket_queue: List[WebSocket] = []

# --- Funciones de ayuda y WebSocket ---

def create_initial_tables():
    """Crea las tablas si no existen"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Base de datos y tablas (contactos, excel_data_universal) verificadas/creadas.")
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_queue.append(websocket)
    print(f"Nuevo cliente WebSocket conectado. Total: {len(websocket_queue)}")
    await websocket.send_json({"type": "status", "message": "Conexión WebSocket establecida."})
    
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        websocket_queue.remove(websocket)
        print(f"Cliente desconectado. Total: {len(websocket_queue)}")

async def broadcast(message: Dict[str, Any]):
    disconnected = []
    for ws in websocket_queue:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in websocket_queue:
            websocket_queue.remove(ws)

@app.on_event("startup")
async def startup_event():
    create_initial_tables()

# --------------------------------------------------------------------
# --- ENDPOINTS PRINCIPALES ---
# --------------------------------------------------------------------

# Mapeo de columnas sucias (con acentos/mayúsculas) a limpias (EXPECTED_COLUMNS)
# Esto asegura que pandas filtre correctamente.
def normalize_column_name(col_name: str) -> str:
    """Normaliza el nombre de columna para la validación y el mapeo."""
    col = str(col_name).strip().lower()
    col = col.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    col = col.replace('ñ', 'n').replace(' ', '')
    return col

@app.post("/upload_and_validate/")
async def upload_and_validate(file: UploadFile = File(...)):
    """
    Sube un Excel, reconoce TODAS sus hojas, valida sus columnas y retorna los datos.
    """
    await broadcast({"type": "log", "message": f"Validando archivo: {file.filename}..."})
    try:
        content = await file.read()
        xls = pd.ExcelFile(io.BytesIO(content))
        
        valid_sheets = []
        invalid_sheets = []
        
        # Las columnas esperadas, normalizadas
        expected_normalized = [normalize_column_name(col) for col in EXPECTED_COLUMNS]

        for sheet_name in xls.sheet_names:
            try:
                # Leer solo la cabecera para la validación
                df_header = pd.read_excel(xls, sheet_name=sheet_name, nrows=0)
                
                # Normalizar columnas del archivo
                actual_normalized = {normalize_column_name(col): col for col in df_header.columns}
                
                # VALIDACIÓN: Comprueba que todas las esperadas estén en las encontradas
                is_valid = all(col in actual_normalized for col in expected_normalized)

                if is_valid:
                    # Si es válida, leemos la hoja completa
                    df_data = pd.read_excel(xls, sheet_name=sheet_name)
                    
                    # Mapeo: Creamos un diccionario para renombrar las columnas del DataFrame
                    # de sucio (archivo) a limpio (base de datos)
                    rename_map = {
                        actual_normalized[expected_col]: expected_col
                        for expected_col in expected_normalized
                        if expected_col in actual_normalized
                    }
                    
                    # Aplicamos el renombrado y seleccionamos solo las columnas de interés
                    df_data.rename(columns=rename_map, inplace=True)
                    
                    # Seleccionamos y reordenamos
                    df_final = df_data[expected_normalized].copy()
                    
                    # Limpieza final: Rellenar NaN con None para mejor JSON/DB manejo
                    df_final = df_final.where(pd.notnull(df_final), None) 
                    
                    # Convertimos a JSON (orient='records' = lista de dicts)
                    data = df_final.to_dict(orient='records')
                    
                    valid_sheets.append({
                        "sheet_name": sheet_name,
                        "data": data,
                        "columns": expected_normalized
                    })
                    await broadcast({"type": "log", "message": f"Hoja '{sheet_name}'... VÁLIDA ({len(data)} filas)."})
                else:
                    invalid_sheets.append({
                        "sheet_name": sheet_name,
                        "columns_found": list(df_header.columns),
                        "columns_expected_normalized": EXPECTED_COLUMNS,
                        "error": "Faltan o sobran columnas requeridas."
                    })
                    await broadcast({"type": "log", "message": f"Hoja '{sheet_name}'... INVÁLIDA."})
            except Exception as e:
                await broadcast({"type": "log", "message": f"Error procesando hoja '{sheet_name}': {e}"})
                invalid_sheets.append({"sheet_name": sheet_name, "error": str(e)})

        await broadcast({"type": "log", "message": "Validación de hojas completada."})
        
        return {
            "filename": file.filename,
            "valid_sheets": valid_sheets,
            "invalid_sheets": invalid_sheets
        }
    except Exception as e:
        error_message = f"Error al leer archivo: {e.__class__.__name__}: {e}"
        await broadcast({"type": "log", "message": f"❌ {error_message}"})
        raise HTTPException(status_code=400, detail=error_message)


@app.post("/save_selected_data/")
async def save_selected_data(data: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """
    Recibe los datos editados (lista plana) y realiza un UPSERT (Merge) en la tabla 'Contacto'.
    """
    if not data:
        raise HTTPException(status_code=400, detail="No se recibieron datos para guardar.")

    await broadcast({"type": "status", "message": "Iniciando carga de datos estructurados..."})
    try:
        total_rows = len(data)
        
        # Usamos EXPECTED_COLUMNS para filtrar y asegurar que solo guardamos datos válidos
        allowed_keys = set(EXPECTED_COLUMNS)

        for i, row_data in enumerate(data):
            try:
                # 1. Filtramos las claves y convertimos los valores de str a int/float si es necesario, 
                # aunque SQLAlchemy suele manejar la conversión
                contact_data = {
                    key: row_data.get(key)
                    for key in allowed_keys
                    if row_data.get(key) is not None and key in row_data
                }

                # 2. Creamos la instancia del modelo Contacto
                new_contact = Contacto(**contact_data)
                
                # 3. UPSERT: Inserta o actualiza por la Llave Primaria (id)
                db.merge(new_contact)
                
            except Exception as e:
                # Log del error en el broadcast y continúa con la siguiente fila
                await broadcast({"type": "log", "message": f"⚠️ Error en fila {i+1} (ID: {row_data.get('id', 'N/A')}): {e}"})
                continue

            # 4. Lógica de Commit y Progreso
            if (i + 1) % 100 == 0:
                db.commit() # Commit por lotes
            
            if (i + 1) % 10 == 0 or (i + 1) == total_rows:
                progress = int(((i + 1) / total_rows) * 100)
                await broadcast({"type": "progress", "value": progress})
                if (i + 1) % 100 == 0 or (i + 1) == total_rows:
                    await broadcast({"type": "log", "message": f"[INFO] {i+1}/{total_rows} filas procesadas. Progreso: {progress}%"})

        db.commit() # Commit final
        await broadcast({"type": "status", "message": f"🎉 ¡Carga finalizada! {total_rows} registros guardados en 'contactos'."})
        return {"status": "success", "message": f"{total_rows} filas guardadas."}
    except Exception as e:
        db.rollback()
        error_message = f"Error durante la inserción: {e.__class__.__name__}: {e}"
        await broadcast({"type": "log", "message": f"❌ {error_message}"})
        raise HTTPException(status_code=500, detail=error_message)


@app.get("/get_contacts_stats/")
async def get_contacts_stats(db: Session = Depends(get_db)):
    """
    Calcula estadísticas para el gráfico de Angular: Conteo total de registros.
    """
    try:
        total_count = db.query(Contacto).count()
        
        # El frontend espera: { labels: [str], data: [number] }
        chart_data = {
            "labels": ["Total Contactos Cargados"],
            "data": [total_count]
        }
        
        return chart_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar estadísticas: {e}")


@app.get("/download_excel/")
async def download_excel(db: Session = Depends(get_db)):
    """
    Descarga los datos de la tabla 'contactos' como Excel.
    """
    try:
        records = db.query(Contacto).all()
        
        # Convertimos la lista de objetos SQLAlchemy a una lista de dicts
        data_list = [
            {
                "id": r.id,
                "nombre": r.nombre,
                "direccion": r.direccion, # Usamos los nombres de la DB
                "telefono": r.telefono,
                "correo": r.correo
            }
            for r in records
        ]
        
        if not data_list:
            raise HTTPException(status_code=404, detail="No hay datos en la base de datos para exportar.")

        df = pd.DataFrame(data_list)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Datos de Contactos', index=False)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename="datos_contactos_db.xlsx"'}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar Excel: {e}")

# --- Mantenemos los endpoints antiguos por si los necesitas, aunque ahora no se usan ---

@app.post("/upload_excel/")
async def upload_excel_old(file: UploadFile = File(...)):
    return {"detail": "Este es el endpoint antiguo. Usa /upload_and_validate/"}


@app.post("/update_and_save/")
async def update_and_save_old(data: List[Dict[str, Any]], db: Session = Depends(get_db)):
    return {"detail": "Este es el endpoint antiguo. Usa /save_selected_data/"}