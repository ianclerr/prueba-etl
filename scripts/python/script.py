'''
    Este es un Script para correr automaticamente los 3 archivos de Python 
    Que realizan el proceso de Carga de datos, Reporte de Ventas y Envio del Email.
'''

import subprocess
import sys

scripts = [
    "scripts/python/cargar_datos.py",
    "scripts/python/reporte_ventas.py",
    "scripts/python/envio_email.py"
]

for script in scripts:
    try:
        print(f"Ejecutando {script}...")
        subprocess.run([sys.executable, script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar {script}: {e}")
        sys.exit(1)

print("Proceso ETL completado exitosamente!")