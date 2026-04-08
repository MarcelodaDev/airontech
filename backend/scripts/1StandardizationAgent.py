import pandas as pd
from pathlib import Path

# 1. Definición de rutas relativas al proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Crear carpeta de salida si no existe
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# 2. Localizar el archivo CSV más reciente generado desde el Excel
csv_files = list(RAW_DIR.glob("*.csv"))
if not csv_files:
    print("Error: No se encontraron archivos CSV en /data/raw.")
    exit()

latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
print(f"Iniciando estandarización con: {latest_file.name}")

# Leer el dataset original
df = pd.read_csv(latest_file)

# 3. Lógica de Estandarización de nombres
# Mapeo de columnas según el esquema del dataset proporcionado
mapeo = {
    'fecha_infraccion': 'fecha',
    'hora_infraccion': 'hora',
    'coordenada_y': 'lat',
    'coordenada_x': 'lon',
    'presunta_motivacion': 'motivacion'
}
df = df.rename(columns=mapeo)

# 4. Selección de características relevantes para el Dashboard [cite: 4]
columnas_mantener = [
    'tipo_muerte', 'provincia', 'canton', 'fecha', 
    'lat', 'lon', 'arma', 'edad', 'sexo', 'etnia', 'motivacion', 'area_hecho'
]
df = df[[c for c in columnas_mantener if c in df.columns]]

# 5. Guardar en la ubicación final (Este archivo será sobreescrito por los siguientes pasos)
# Se usa 'dataset_final.csv' como nombre estándar para el Dashboard
output_path = PROCESSED_DIR / "dataset_final.csv"
df.to_csv(output_path, index=False, encoding="utf-8")

print(f"Paso 1 completado: Archivo creado en {output_path}")