import os
import json
import subprocess
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hackaton Data Ecuador API")

# Configuración de CORS: Permite que el frontend acceda a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definición de rutas dinámicas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA = os.path.join(BASE_DIR, "data", "processed", "dataset_final.csv")
COORDS_DATA = os.path.join(BASE_DIR, "data", "processed", "coordenadas.json")

# LOG inicial para depuración
print(f"Ruta base detectada: {BASE_DIR}")
print(f"Buscando CSV en: {PROCESSED_DATA}")
print(f"Buscando JSON en: {COORDS_DATA}")

@app.get("/")
async def root():
    return {
        "status": "online",
        "csv_exists": os.path.exists(PROCESSED_DATA),
        "coords_exists": os.path.exists(COORDS_DATA)
    }

@app.get("/api/datos-mapa")
async def obtener_mapa():
    """Retorna datos georreferenciados para el mapa"""
    if not os.path.exists(PROCESSED_DATA):
        raise HTTPException(status_code=404, detail="Archivo dataset_final.csv no encontrado. Ejecuta el procesamiento primero.")
    if not os.path.exists(COORDS_DATA):
        raise HTTPException(status_code=404, detail="Archivo coordenadas.json no encontrado.")

    try:
        # Cargar datos
        df = pd.read_csv(PROCESSED_DATA)
        with open(COORDS_DATA, "r", encoding="utf-8") as f:
            coords = json.load(f)

        # Normalizar claves del JSON a mayúsculas para facilitar la búsqueda
        coords_normalized = {k.upper().strip(): v for k, v in coords.items()}

        map_data = []
        for _, row in df.iterrows():
            # Intentar obtener el cantón (debe coincidir con las llaves en coordenadas.json)
            canton_name = str(row.get("Cantón", "")).strip().upper()
            
            if canton_name in coords_normalized:
                pos = coords_normalized[canton_name]
                map_data.append({
                    "lat": pos["lat"],
                    "lon": pos["lon"],
                    "provincia": row.get("Provincia", "N/A"),
                    "canton": row.get("Cantón", "N/A"),
                    "tipo": row.get("Tipo de muerte", "N/A"),
                    "arma": row.get("Arma", "N/A"),
                    "fecha": str(row.get("Fecha", "N/A"))
                })
        
        return map_data

    except Exception as e:
        print(f"Error en /api/datos-mapa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando datos: {str(e)}")

@app.get("/api/datos")
async def obtener_datos():
    """Retorna los últimos 100 registros para mostrar en tablas"""
    if not os.path.exists(PROCESSED_DATA):
        return []
    try:
        df = pd.read_csv(PROCESSED_DATA)
        return df.tail(100).fillna("N/A").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kpis")
async def kpis():
    """Retorna métricas de resumen clave para el dashboard"""
    if not os.path.exists(PROCESSED_DATA):
        return {"total_filas": 0}
    df = pd.read_csv(PROCESSED_DATA)
    return {
        "total_filas": len(df),
        "total_columnas": len(df.columns),
        "num_provincias": df["provincia"].nunique() if "provincia" in df else 0,
        "nulos_totales": int(df.isnull().sum().sum()),
        "columnas": list(df.columns)
    }

@app.get("/api/univariate/{columna}")
async def univariate(columna: str):
    if not os.path.exists(PROCESSED_DATA):
        return {"labels": [], "data": []}
    df = pd.read_csv(PROCESSED_DATA)
    if columna not in df.columns:
        raise HTTPException(status_code=400, detail="Columna no existe")
    
    counts = df[columna].value_counts().head(10)
    return {
        "labels": counts.index.astype(str).tolist(),
        "data": counts.values.tolist()
    }

@app.get("/api/correlation")
async def correlation():
    if not os.path.exists(PROCESSED_DATA):
        return {"columns": [], "matrix": []}
    df = pd.read_csv(PROCESSED_DATA)
    # Seleccionar solo columnas numéricas
    df_num = df.select_dtypes(include=['number'])
    # Reemplazar NaN en el DataFrame antes de correlación si tiene varianza
    if df_num.empty:
        return {"columns": [], "matrix": []}
    
    corr = df_num.corr().fillna(0)
    cols = corr.columns.tolist()
    matrix = corr.values.tolist()
    return {"columns": cols, "matrix": matrix}

@app.get("/api/bivariate")
async def bivariate(col_x: str, col_y: str):
    if not os.path.exists(PROCESSED_DATA):
        return []
    df = pd.read_csv(PROCESSED_DATA)
    if col_x not in df.columns or col_y not in df.columns:
        raise HTTPException(status_code=400, detail="Columna(s) no existe(n)")
    
    # Manejar "SIN_DATO" u otros en numéricos. Convertir a numérico donde aplicable
    df_clean = df[[col_x, col_y]].dropna()
    df_clean[col_x] = pd.to_numeric(df_clean[col_x], errors='coerce')
    df_clean[col_y] = pd.to_numeric(df_clean[col_y], errors='coerce')
    df_clean = df_clean.dropna()

    # Si pasamos demasiados puntos, muestrear a 1000 para graficar rápido
    if len(df_clean) > 1000:
        df_clean = df_clean.sample(1000)

    records = df_clean.rename(columns={col_x: "x", col_y: "y"}).to_dict(orient="records")
    return records

@app.post("/api/procesar-dataset")
async def procesar_dataset():
    """Ejecuta los agentes de limpieza y georreferenciación en orden"""
    scripts = [
        "1StandardizationAgent.py", 
        "2DeepCleaningAgent.py", 
        "3FilterAgent.py", 
        "4GeoreferenceAgent.py"
    ]
    
    resultados = []
    try:
        for script in scripts:
            script_path = os.path.join(BASE_DIR, "scripts", script)
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"No se encontró el script: {script}")
            
            # Ejecutar script
            subprocess.run(["python", script_path], check=True)
            resultados.append(f"Ejecutado: {script}")
            
        return {"status": "success", "steps": resultados}
    except Exception as e:
        print(f"Fallo en pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ejecutando scripts: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Ejecución del servidor
    uvicorn.run(app, host="127.0.0.1", port=8000)