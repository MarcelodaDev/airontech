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
        return {}
    df = pd.read_csv(PROCESSED_DATA)
    if col_x not in df.columns or col_y not in df.columns:
        raise HTTPException(status_code=400, detail="Columna(s) no existe(n)")
    
    df_clean = df[[col_x, col_y]].dropna()
    if df_clean.empty:
        return {"error": "Sin datos"}

    is_x_num = pd.api.types.is_numeric_dtype(df_clean[col_x])
    is_y_num = pd.api.types.is_numeric_dtype(df_clean[col_y])

    # Convertir a string si no son numéricos, para evitar fallos de agrupamiento
    if not is_x_num:
        df_clean[col_x] = df_clean[col_x].astype(str)
    if not is_y_num:
        df_clean[col_y] = df_clean[col_y].astype(str)

    if is_x_num and is_y_num:
        # Scatter Numérico vs Numérico
        if len(df_clean) > 1000:
            df_clean = df_clean.sample(1000)
        records = df_clean.rename(columns={col_x: "x", col_y: "y"}).to_dict(orient="records")
        return {"type": "scatter", "data": records}
        
    elif not is_x_num and not is_y_num:
        # Categorico vs Categorico -> Cantidades (Stacked Bar)
        top_x = df_clean[col_x].value_counts().head(10).index
        top_y = df_clean[col_y].value_counts().head(6).index
        
        filtered = df_clean[df_clean[col_x].isin(top_x) & df_clean[col_y].isin(top_y)]
        grouped = filtered.groupby([col_x, col_y]).size().unstack(fill_value=0)
        
        labels_x = grouped.index.tolist()
        datasets = []
        for y_cat in grouped.columns:
            datasets.append({
                "label": str(y_cat),
                "data": grouped[y_cat].tolist()
            })
            
        return {
            "type": "stacked_bar",
            "labels": [str(l) for l in labels_x],
            "datasets": datasets
        }
        
    else:
        # Mixto: Uno categórico y otro numérico -> Promedio (Bar)
        cat_col = col_x if not is_x_num else col_y
        num_col = col_y if not is_x_num else col_x
        
        top_cat = df_clean[cat_col].value_counts().head(12).index
        filtered = df_clean[df_clean[cat_col].isin(top_cat)]
        
        grouped = filtered.groupby(cat_col)[num_col].mean().sort_values(ascending=False)
        return {
            "type": "bar",
            "labels": [str(l) for l in grouped.index],
            "data": grouped.values.tolist(),
            "x_label": cat_col,
            "y_label": f"Promedio de {num_col}"
        }

@app.get("/api/storytelling")
async def storytelling():
    if not os.path.exists(PROCESSED_DATA):
        return {"html": "<p>Aún no hay datos procesados.</p>"}
    
    try:
        df = pd.read_csv(PROCESSED_DATA)
        # Normalización básica para búsqueda
        cols_lower = {c.lower(): c for c in df.columns}
        
        prov_col = cols_lower.get("provincia", cols_lower.get("provincias", None))
        canton_col = cols_lower.get("cantón", cols_lower.get("canton", cols_lower.get("cantones", None)))
        
        insights = ""
        
        if prov_col:
            top_prov = df[prov_col].value_counts().head(5)
            total = len(df)
            top_prov_sum = top_prov.sum()
            perc = (top_prov_sum / total) * 100 if total > 0 else 0
            
            insights += f"""
            <div class='insight-card'>
                <h4 style="color: #2c7da0; margin-bottom: 0.5rem;">🚨 Concentración Provincial de Riesgo</h4>
                <p>Las 5 provincias con mayor incidencia criminal agrupan el <strong>{perc:.1f}%</strong> del total a nivel nacional ({top_prov_sum} de {total} casos registrados).
                El ranking está liderado por: <strong>{', '.join(top_prov.index.tolist())}</strong>. 
                Esto confirma el patrón de alta violencia geográficamente focalizada que demanda la redistribución de recursos de seguridad.</p>
            </div>
            """
            
        if canton_col:
            top_canton = df[canton_col].value_counts().head(3)
            # Solo si encontramos al menos tres cantones válidos
            if len(top_canton) >= 3:
                insights += f"""
                <div class='insight-card' style="margin-top: 1rem;">
                    <h4 style="color: #2c7da0; margin-bottom: 0.5rem;">⚠️ Cantones Críticos e Intervención</h4>
                    <p>Tras analizar transversalmente la distribución, los 3 cantones de mayor riesgo absoluto para despliegue táctico-policial preventivo son: 
                    <strong>{top_canton.index[0]}</strong> ({top_canton.iloc[0]} eventos), 
                    <strong>{top_canton.index[1]}</strong> ({top_canton.iloc[1]} eventos) y 
                    <strong>{top_canton.index[2]}</strong> ({top_canton.iloc[2]} eventos).</p>
                </div>
                """
        
        if not insights:
            insights = "<p>El dataset procesado no contenía columnas geográficas claras ('Provincia', 'Cantón') para emitir conclusiones geoespaciales precisas. Utiliza el módulo Bivariado Dinámico para exploraciones personalizadas.</p>"
            
        return {"html": insights}
    except Exception as e:
        return {"html": f"<p style='color:red;'>Error generando IA insights: {str(e)}</p>"}

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