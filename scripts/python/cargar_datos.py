import pandas as pd
from sqlalchemy import create_engine, text, inspect
import os
from openpyxl import load_workbook

# Configuración
DB_CONFIG = {
    "host": "localhost",
    "database": "test_etl",
    "user": "postgres",
    "password": "root",
    "port": "5432"
}

EXCEL_PATH = "./data/input/datos_fuente.xlsx"

def verificar_archivo_excel():
    """Verifica que el archivo Excel existe y contiene las hojas necesarias"""
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Archivo no encontrado: {EXCEL_PATH}")
    
    wb = load_workbook(EXCEL_PATH)
    hojas_disponibles = wb.sheetnames
    hojas_requeridas = ['clientes', 'productos', 'ventas']
    
    for hoja in hojas_requeridas:
        if hoja not in hojas_disponibles:
            raise ValueError(f"Hoja requerida '{hoja}' no encontrada en el Excel")
    
    return True

def limpiar_tablas(engine):
    """Elimina datos existentes manteniendo la estructura de tablas"""
    tablas = ['ventas', 'productos', 'clientes']  # Orden inverso por dependencias
    
    with engine.begin() as conn:
        for tabla in tablas:
            try:
                conn.execute(text(f"TRUNCATE TABLE {tabla} RESTART IDENTITY CASCADE"))
                print(f"♻️ Tabla '{tabla}' limpiada (datos eliminados)")
            except Exception as e:
                print(f"⚠️ No se pudo limpiar tabla '{tabla}': {str(e)}")

def cargar_datos(engine, sheet_name):
    """Carga datos desde una hoja específica a PostgreSQL"""
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
        
        # Verificar que el DataFrame no esté vacío
        if df.empty:
            print(f"⚠️ Hoja '{sheet_name}' está vacía")
            return False
        
        # Cargar datos a PostgreSQL
        df.to_sql(
            name=sheet_name,
            con=engine,
            if_exists="append",
            index=False
        )
        
        print(f"✅ Datos cargados en '{sheet_name}' ({len(df)} registros)")
        return True
        
    except Exception as e:
        print(f"❌ Error al cargar '{sheet_name}': {str(e)}")
        return False

def main():
    print("\n=== IMPORTADOR DE DATOS DE EXCEL A POSTGRESQL ===")
    print(f"Archivo fuente: {EXCEL_PATH}")
    
    try:
        # 1. Verificar archivo Excel
        verificar_archivo_excel()
        
        # 2. Conectar a PostgreSQL
        engine = create_engine(
            f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        
        # 3. Limpiar tablas existentes
        limpiar_tablas(engine)
        
        # 4. Cargar datos en el orden correcto
        orden_carga = ['clientes', 'productos', 'ventas']
        resultados = []
        
        for tabla in orden_carga:
            resultados.append(cargar_datos(engine, tabla))
        
        # 5. Resumen final
        if all(resultados):
            print("\n✔️ Todos los datos se cargaron exitosamente")
        else:
            print("\n⚠️ Algunos datos no se cargaron correctamente")
            
    except Exception as e:
        print(f"\n❌ Error crítico: {str(e)}")
    finally:
        if 'engine' in locals():
            engine.dispose()
            print("\nConexión a PostgreSQL cerrada")

if __name__ == "__main__":
    main()