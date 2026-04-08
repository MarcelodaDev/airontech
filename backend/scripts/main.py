import subprocess
import sys
from pathlib import Path

# Configuración de rutas
SCRIPT_DIR = Path(__file__).resolve().parent

# Definición del Pipeline en orden secuencial
PIPELINE = [
    "0convertirCSV.py",
    "1StandardizationAgent.py",
    "2DeepCleaningAgent.py",
    "3FilterAgent.py",
    "4GeoreferenceAgent.py"
    "5TimeAndDemographicsAgent.py"
]

def run_script(script_name):
    """Ejecuta un script individual y retorna su éxito."""
    script_path = SCRIPT_DIR / script_name
    
    print(f"\n>>> EJECUTANDO: {script_name}...")
    
    try:
        # Ejecutamos el script usando el mismo intérprete de Python del venv
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False, # Permite ver los print() de cada script en consola
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f" ERROR en {script_name}: El proceso se detuvo.")
        return False

def main():
    print("====================================================")
    print("   INICIANDO PIPELINE DE PROCESAMIENTO IABOYS")
    print("====================================================")

    for i, script in enumerate(PIPELINE):
        print(f"\n[PASO {i}/4]")
        success = run_script(script)
        
        if not success:
            print("\n FALLO CRÍTICO: El pipeline ha sido abortado.")
            sys.exit(1)

    print("\n====================================================")
    print("   PIPELINE FINALIZADO CON ÉXITO")
    print("   Archivo listo en: /data/processed/dataset_final.csv")
    print("====================================================")

if __name__ == "__main__":
    main()