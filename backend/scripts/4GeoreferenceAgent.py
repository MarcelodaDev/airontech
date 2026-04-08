import pandas as pd
import numpy as np
import json
import unicodedata
from pathlib import Path

<<<<<<< HEAD
# --- CONFIGURACIÓN DE RUTAS RELATIVAS ---
# BASE_DIR apunta a la raíz del proyecto (IABoys)
BASE_DIR = Path(__file__).resolve().parent.parent
# Ruta al JSON de coordenadas en data/processed
JSON_PATH = BASE_DIR / "data" / "processed" / "coordenadas.json"
# Archivo de datos final en data/processed
=======
# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = Path(__file__).resolve().parent.parent
JSON_PATH = BASE_DIR / "data" / "processed" / "coordenadas.json"
>>>>>>> b1fd096 (frontend)
FILE_PATH = BASE_DIR / "data" / "processed" / "dataset_final.csv"

def normalizar_texto(texto):
    """Normaliza texto: mayúsculas y quita tildes para asegurar cruces."""
    if pd.isna(texto): return texto
    texto = str(texto).upper().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn')
    return texto

def cargar_json_coordenadas():
    """Carga el diccionario desde el archivo JSON usando la ruta relativa."""
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"CRÍTICO: No se encontró el archivo JSON en {JSON_PATH}")
        return {}

def imputar_geo():
    try:
        if not FILE_PATH.exists():
            print(f"Error: No existe el archivo en {FILE_PATH}")
            return
        
        # Carga del dataset desde la carpeta processed
        df = pd.read_csv(FILE_PATH)

        # Identificación dinámica de columnas
        col_lat = 'lat' if 'lat' in df.columns else 'latitud'
        col_lon = 'lon' if 'lon' in df.columns else 'longitud'
        
        print(f"Procesando imputación en: {col_lat}, {col_lon}")

        # Identificar nulos originales para el reporte final
        mask_nulos_init = (df[col_lat].isna()) | (df[col_lat] == 0.0)

        # Normalización de categorías para el agrupamiento
        df['provincia'] = df['provincia'].apply(normalizar_texto)
        df['canton'] = df['canton'].apply(normalizar_texto)
        
        # Limpieza de valores inválidos antes del cálculo
        df[col_lat] = df[col_lat].replace(0.0, np.nan)
        df[col_lon] = df[col_lon].replace(0.0, np.nan)

        # 1. Imputación por Cantón (Media local)
        df[col_lat] = df[col_lat].fillna(df.groupby('canton')[col_lat].transform('mean'))
        df[col_lon] = df[col_lon].fillna(df.groupby('canton')[col_lon].transform('mean'))

        # 2. Imputación por Provincia (Media regional)
        df[col_lat] = df[col_lat].fillna(df.groupby('provincia')[col_lat].transform('mean'))
        df[col_lon] = df[col_lon].fillna(df.groupby('provincia')[col_lon].transform('mean'))

        # 3. Media Global del dataset
        df[col_lat] = df[col_lat].fillna(df[col_lat].mean())
        df[col_lon] = df[col_lon].fillna(df[col_lon].mean())

        # 4. Fallback final mediante JSON de referencia
        fallback_dict = cargar_json_coordenadas()
        indices_nulos = df[df[col_lat].isna()].index
        for idx in indices_nulos:
            prov = df.at[idx, 'provincia']
            if prov in fallback_dict:
                df.at[idx, col_lat] = fallback_dict[prov][0]
                df.at[idx, col_lon] = fallback_dict[prov][1]

        # Sobrescritura del archivo final para el Dashboard
        imputados = mask_nulos_init.sum() - df[col_lat].isna().sum()
        df.to_csv(FILE_PATH, index=False, encoding="utf-8")

        print("==========================================")
        print(f"REGISTROS REPARADOS: {imputados}")
        print(f"Archivo actualizado: {FILE_PATH.name}")
        print("==========================================")

    except Exception as e:
        print(f"Error en el proceso: {e}")

if __name__ == "__main__":
    imputar_geo()