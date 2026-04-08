import pandas as pd
from pathlib import Path

# Definir rutas relativas al proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_DIR = BASE_DIR / "data" / "excel"
OUTPUT_DIR = BASE_DIR / "data" / "raw"

# Crear carpeta output si no existe
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Buscar archivos Excel
excel_files = list(EXCEL_DIR.glob("*.xlsx")) + list(EXCEL_DIR.glob("*.xls"))

if not excel_files:
    print("No hay archivos Excel en la carpeta /data/excel")
    exit()

# Tomar el más reciente
latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)

print(f"Archivo detectado: {latest_file.name}")

# Leer Excel
df = pd.read_excel(latest_file)

# Nombre del CSV basado en el Excel
output_file = OUTPUT_DIR / (latest_file.stem + ".csv")

# Guardar CSV
df.to_csv(output_file, index=False, encoding="utf-8")

print(f"Convertido a CSV: {output_file}")