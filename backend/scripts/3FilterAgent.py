import pandas as pd
from pathlib import Path

# 1. Configuración de rutas relativas
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FILE_PATH = PROCESSED_DIR / "dataset_final.csv"

# Verificar que el archivo del paso anterior exista
if not FILE_PATH.exists():
    print("Error: No se encuentra 'dataset_final.csv'. Ejecuta primero el Paso 2.")
    exit()

# Leer el dataset actual de la carpeta processed
df = pd.read_csv(FILE_PATH)

# 2. Lógica de Filtrado Temporal (2022-2024)
if 'fecha' in df.columns:
    # Convertir a datetime para poder extraer el año
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    
    # Eliminar registros donde la fecha no pudo ser convertida (datos basura)
    df = df.dropna(subset=['fecha'])
    
    # Filtrar el rango solicitado para el Dashboard
    df = df[(df['fecha'].dt.year >= 2022) & (df['fecha'].dt.year <= 2024)]

# 3. SOBRESCRITURA DEL ARCHIVO FINAL
# El Dashboard consumirá este archivo directamente
df.to_csv(FILE_PATH, index=False, encoding="utf-8")

print(f"Paso 3 completado: Filtro 2022-2024 aplicado.")
print(f"Registros finales: {len(df)}")
print(f"ARCHIVO FINAL ACTUALIZADO EN: {FILE_PATH}")