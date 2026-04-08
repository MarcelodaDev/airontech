import pandas as pd
import json
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FILE_PATH = PROCESSED_DIR / "dataset_final.csv"
POBLACION_PATH = PROCESSED_DIR / "poblacion.json"

def clasificar_franja(hora_str):
    """Clasifica la hora en categorías operativas."""
    try:
        h = pd.to_datetime(hora_str, format='%H:%M:%S').hour
        if 0 <= h < 6: return 'MADRUGADA'
        if 6 <= h < 12: return 'MAÑANA'
        if 12 <= h < 18: return 'TARDE'
        return 'NOCHE'
    except:
        return 'NO DETERMINADO'

def procesar_inteligencia():
    if not FILE_PATH.exists() or not POBLACION_PATH.exists():
        print("Error: Faltan archivos base (dataset_final o poblacion.json)")
        return

    df = pd.read_csv(FILE_PATH)
    
    # 1. Inteligencia Temporal
    df['fecha'] = pd.to_datetime(df['fecha'])
    dias_es = {
        'Monday': 'LUNES', 'Tuesday': 'MARTES', 'Wednesday': 'MIERCOLES',
        'Thursday': 'JUEVES', 'Friday': 'VIERNES', 'Saturday': 'SABADO', 'Sunday': 'DOMINGO'
    }
    df['dia_nombre'] = df['fecha'].dt.day_name().map(dias_es)
    df['franja_horaria'] = df['hora'].apply(clasificar_franja)

    # 2. Normalización Demográfica (Tasas)
    with open(POBLACION_PATH, 'r', encoding='utf-8') as f:
        data_poblacion = json.load(f)
    
    # Contar homicidios por provincia
    conteo_prov = df['provincia'].value_counts().to_dict()
    
    # Calcular Tasa (Homicidios / Población * 100,000)
    # Creamos un diccionario de tasas para mapear al DF
    tasas_dict = {}
    for prov, pop in data_poblacion.items():
        # Normalizamos el nombre de la provincia para el cruce
        prov_norm = prov.upper()
        casos = conteo_prov.get(prov_norm, 0)
        tasas_dict[prov_norm] = round((casos / pop) * 100000, 2) if pop > 0 else 0

    df['tasa_provincial'] = df['provincia'].map(tasas_dict)

    # 3. Guardar cambios (Sobrescritura)
    df.to_csv(FILE_PATH, index=False, encoding="utf-8")
    print(f"Paso 5 completado: Inteligencia temporal y tasas demográficas añadidas.")
    print(f"Tasa máxima detectada: {df['tasa_provincial'].max()}")

if __name__ == "__main__":
    procesar_inteligencia()