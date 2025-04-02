"""
SCRIPT DE REPORTE DE VENTAS POR CONSOLA Y GENERACIÓN DE EXCEL

Este script genera:
1. Un reporte resumido de ventas en la consola
2. Un archivo Excel con el reporte detallado en data/output

Funcionalidades:
1- Muestra título del reporte en consola
2- Se conecta a la BD PostgreSQL
3- Detecta automáticamente el rango de fechas
4- Obtiene ventas con info de clientes y productos
5- Calcula métricas (total facturado, productos/cliente destacado)
6- Muestra reporte en consola
7- Genera archivo Excel en data/output
8- Cierra conexión automáticamente
"""

import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import sys
from pathlib import Path
import os

# Añadir el directorio raíz al path para importar configuraciones
sys.path.append(str(Path(__file__).parent.parent.parent))

# Importar configuración de base de datos
from config.database import DB_CONFIG, get_db_uri

def obtener_rango_fechas(engine):
    """
    Obtiene el rango real de fechas disponible en la base de datos.
    
    Args:
        engine: Conexión SQLAlchemy a la base de datos.
        
    Returns:
        tuple: (fecha_min, fecha_max) -> Fecha mínima y máxima en la tabla ventas.
    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MIN(fecha), MAX(fecha) FROM ventas"))
        return result.fetchone()

def generar_excel_reporte(df, fecha_min, fecha_max):
    """
    Genera un archivo Excel con el reporte de ventas en data/output
    
    Args:
        df: DataFrame con los datos de ventas
        fecha_min: Fecha inicio del período
        fecha_max: Fecha fin del período
        
    Returns:
        str: Ruta del archivo generado
    """
    # Crear directorio si no existe
    os.makedirs('data/output', exist_ok=True)
    
    # Nombre del archivo con rango de fechas
    nombre_archivo = f"data/output/reporte_ventas_{fecha_min.strftime('%Y%m%d')}_{fecha_max.strftime('%Y%m%d')}.xlsx"
    
    # Generar Excel
    with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Ventas')
        
        # Obtener objetos para formateo
        workbook = writer.book
        worksheet = writer.sheets['Ventas']
        
        # Formatear columnas
        for cell in worksheet['B'][1:]:  # Columna de fechas
            cell.number_format = 'DD/MM/YYYY'
            
        for cell in worksheet['D'][1:]:  # Columna de montos
            cell.number_format = '"Gs."#,##0'
        
        # Ajustar anchos de columnas
        worksheet.column_dimensions['A'].width = 12  # Fecha
        worksheet.column_dimensions['B'].width = 25  # Cliente
        worksheet.column_dimensions['C'].width = 25  # Producto
        worksheet.column_dimensions['D'].width = 15  # Monto
    
    print(f"\n📊 Reporte Excel generado: {nombre_archivo}")
    return nombre_archivo

def generar_reporte_consola():
    """
    Genera y muestra el reporte en consola y genera archivo Excel.
    """
    try:
        # 1. Conexión a la base de datos
        engine = create_engine(get_db_uri())
        print("\n✅ Conexión exitosa a PostgreSQL")
        
        # 2. Obtener rango de fechas
        fecha_min, fecha_max = obtener_rango_fechas(engine)
        print(f"\nℹ️ Rango de fechas disponible: {fecha_min} a {fecha_max}")
        
        # 3. Consultar datos de ventas
        query = text("""
        SELECT 
            v.fecha,
            c.nombre AS cliente,
            p.nombre AS producto,
            v.monto_total
        FROM ventas v
        JOIN clientes c ON v.cliente_id = c.cliente_id
        JOIN productos p ON v.producto_id = p.producto_id
        WHERE v.fecha BETWEEN :fecha_inicio AND :fecha_fin
        ORDER BY v.fecha DESC
        """)
        
        with engine.connect() as conn:
            df = pd.read_sql(
                query, 
                conn,
                params={"fecha_inicio": fecha_min, "fecha_fin": fecha_max}
            )
            
            if df.empty:
                print("\n⚠️ No hay ventas en el período disponible")
                return
            
            # 4. Calcular métricas
            total_facturado = df['monto_total'].sum()
            producto_top = df.groupby('producto')['monto_total'].sum().idxmax()
            monto_producto = df.groupby('producto')['monto_total'].sum().max()
            cliente_top = df.groupby('cliente')['monto_total'].sum().idxmax()
            monto_cliente = df.groupby('cliente')['monto_total'].sum().max()
            
            # 5. Mostrar reporte en consola
            print("\n" + "="*50)
            print("REPORTE DE VENTAS - RESUMEN".center(50))
            print("="*50)
            print(f"\nFECHA: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            print(f"PERÍODO ANALIZADO: {fecha_min.strftime('%d/%m/%Y')} al {fecha_max.strftime('%d/%m/%Y')}")
            print("\nMÉTRICAS PRINCIPALES")
            print("-"*20)
            print(f"* TOTAL FACTURADO: Gs. {total_facturado:,.0f}")
            print(f"* PRODUCTO DESTACADO: {producto_top} (Gs. {monto_producto:,.0f})")
            print(f"* CLIENTE DESTACADO: {cliente_top} (Gs. {monto_cliente:,.0f})")
            print("\n" + "="*50)
            print(f"Total de ventas analizadas: {len(df)}")
            print("="*50)
            
            # 6. Generar archivo Excel
            generar_excel_reporte(df, fecha_min, fecha_max)
            
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("SISTEMA DE REPORTES DE VENTAS".center(50))
    print("="*50)
    generar_reporte_consola()