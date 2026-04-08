import pandas as pd
from pathlib import Path

# 1. Configuración de rutas relativas
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FILE_PATH = PROCESSED_DIR / "dataset_final.csv"

# Verificar que el archivo del paso anterior exista
if not FILE_PATH.exists():
    print("Error: No se encuentra 'dataset_final.csv'. Ejecuta primero el Paso 1.")
    exit()

# Leer el dataset actual de la carpeta processed
df = pd.read_csv(FILE_PATH)

# 2. Eliminación de columnas no relevantes (según tu lista)
columnas_a_quitar = [
    'codigo_provincia', 'codigo_canton', 'codigo_subcircuito', 
    'circuito', 'subcircuito', 'zona', 'hora', 'subzona', 'profesion_registro_civil', 
    'instruccion', 'estado_civil', 'discapacidad', 'genero', 
    'lugar', 'tipo_lugar', 'distrito'
]

# Filtrar solo las que existen para evitar errores
df = df.drop(columns=[col for col in columnas_a_quitar if col in df.columns])

# 3. Lógica de Limpieza Profunda
# Corregir comas en lat/lon (ej: "-0,35" -> "-0.35")
for col in ['lat', 'lon']:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce')

# 4. Normalizar texto (Mayúsculas y sin espacios extra)
columnas_obj = df.select_dtypes(include=['object']).columns
for col in columnas_obj:
    df[col] = df[col].astype(str).str.strip().str.upper()

# 5. SOBRESCRITURA DEL ARCHIVO FINAL
df.to_csv(FILE_PATH, index=False, encoding="utf-8")

print(f"Paso 2 completado: Columnas eliminadas y formatos corregidos en {FILE_PATH.name}")
print(f"Columnas restantes: {list(df.columns)}")