# backend/main.py

import os
import io
import json
import sys
from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd

# Asegurar path para imports locales
# Nota: Asume que database.py está en el mismo directorio.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importación de database.py
import database
from database import get_db, ExcelRow, Base, engine

# Inicialización de FastAPI
app = FastAPI(title="Excel Uploader API")

# Crea las tablas (si no existen) al inicio del script
Base.metadata.create_all(bind=engine)

# --------------------------
# Configuración CORS AJUSTADA
# --------------------------
# ¡CRÍTICO! Definir explícitamente los orígenes permitidos para tu frontend (8080)
origins = [
    "http://localhost:8080", 
    "http://127.0.0.1:8080",
    # Puedes añadir más si usas host.docker.internal, etc.
]  
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite GET, POST, etc.
    allow_headers=["*"], # Permite todos los encabezados
)
# --------------------------

# Cola global WebSocket
websocket_queue: List[WebSocket] = []

# --- Funciones de ayuda ---
def create_initial_tables():
    """Crea las tablas si no existen"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Base de datos y tablas verificadas/creadas.")
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")

# --- WebSocket ---
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

# --- Startup ---
@app.on_event("startup")
async def startup_event():
    create_initial_tables()

# --- Endpoints ---
@app.post("/upload_excel/")
async def upload_excel(file: UploadFile = File(...)):
    """Sube archivo Excel y devuelve JSON limpio"""
    await broadcast({"type": "log", "message": f"Subiendo archivo: {file.filename}..."})
    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(' ', '_')

        # Mapeo opcional
        column_mapping = {'nombre': 'name', 'producto': 'name', 'descripcion': 'name', 'precio': 'price', 'costo': 'price'}
        cols_to_rename = {k: v for k, v in column_mapping.items() if k in df.columns}
        df.rename(columns=cols_to_rename, inplace=True)

        df_final = df.copy()
        await broadcast({"type": "log", "message": f"Archivo leído. {len(df_final)} filas."})

        data = json.loads(df_final.to_json(orient='records', date_format='iso'))
        await broadcast({"type": "log", "message": "Datos listos para edición."})
        return {"filename": file.filename, "data": data, "columns": df_final.columns.tolist()}
    except Exception as e:
        error_message = f"Error al leer archivo: {e.__class__.__name__}: {e}"
        await broadcast({"type": "log", "message": f"❌ {error_message}"})
        raise HTTPException(status_code=400, detail=error_message)

@app.post("/update_and_save/")
async def update_and_save(data: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """Guarda los datos editados en la DB"""
    if not data:
        raise HTTPException(status_code=400, detail="No se recibieron datos para guardar.")

    await broadcast({"type": "status", "message": "Iniciando carga de datos..."})
    try:
        db.query(ExcelRow).delete()
        db.commit()

        total_rows = len(data)
        for i, row_data in enumerate(data):
            try:
                row_json = json.dumps(row_data)
                new_row = ExcelRow(row_content_json=row_json)
                db.add(new_row)
            except Exception as e:
                await broadcast({"type": "log", "message": f"⚠️ Error fila {i+1}: {e}"})
                continue

            if (i + 1) % 100 == 0:
                db.commit()

            if (i + 1) % 10 == 0 or (i + 1) == total_rows:
                progress = int(((i + 1) / total_rows) * 100)
                await broadcast({"type": "progress", "value": progress})
                await broadcast({"type": "log", "message": f"[INFO] {i+1}/{total_rows} filas procesadas. Progreso: {progress}%"})

        db.commit()
        await broadcast({"type": "status", "message": f"🎉 ¡Carga finalizada! {total_rows} registros guardados."})
        return {"status": "success", "message": f"{total_rows} filas guardadas."}
    except Exception as e:
        db.rollback()
        error_message = f"Error durante la inserción masiva: {e.__class__.__name__}: {e}"
        await broadcast({"type": "log", "message": f"❌ {error_message}"})
        raise HTTPException(status_code=500, detail=error_message)

@app.get("/download_excel/")
async def download_excel(db: Session = Depends(get_db)):
    """Descarga los datos de la DB como Excel"""
    try:
        records = db.query(ExcelRow).all()
        data_list = [json.loads(r.row_content_json) | {"db_id": r.id} for r in records]
        df = pd.DataFrame(data_list)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Datos Editados', index=False)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename="datos_editados_flex.xlsx"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar Excel: {e}")