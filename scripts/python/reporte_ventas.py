import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar configuraciones
sys.path.append(str(Path(__file__).parent.parent.parent))

# Importar configuración de base de datos
from config.database import DB_CONFIG, get_db_uri

def obtener_rango_fechas(engine):
    """
    Obtiene el rango real de fechas disponible en la base de datos
    
    Args:
        engine: Conexión SQLAlchemy a la base de datos
        
    Returns:
        tuple: (fecha_min, fecha_max)
    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MIN(fecha), MAX(fecha) FROM ventas"))
        return result.fetchone()

def generar_reporte_consola():
    """
    Genera y muestra el reporte directamente en la consola
    
    Proceso:
    1. Establece conexión con la base de datos
    2. Obtiene el rango de fechas disponible
    3. Consulta los datos de ventas
    4. Calcula métricas clave
    5. Muestra el reporte formateado en consola
    """
    try:
        # 1. Conexión a la base de datos
        engine = create_engine(get_db_uri())
        print("\n✅ Conexión exitosa a PostgreSQL")
        
        # 2. Obtener rango de fechas
        fecha_min, fecha_max = obtener_rango_fechas(engine)
        print(f"\nℹ️ Rango de fechas disponible: {fecha_min} a {fecha_max}")
        
        # 3. Consultar datos
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
            
            # 5. Mostrar reporte
            print("\n" + "="*50)
            print("REPORTE DE VENTAS - RESUMEN".center(50))
            print("="*50)
            print(f"\nFECHA: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            print(f"PERÍODO ANALIZADO: {fecha_min.strftime('%d/%m/%Y')} al {fecha_max.strftime('%d/%m/%Y')}")
            print("\nMÉTRICAS PRINCIPALES")
            print("-"*20)
            print(f"* TOTAL FACTURADO: Gs. {total_facturado:,.0f}")
            print(f"* PRODUCTO DESTACADO: {producto_top}")
            print(f"* CLIENTE DESTACADO: {cliente_top} (Gs. {monto_cliente:,.0f})")
            print("\n" + "="*50)
            print(f"Total de ventas analizadas: {len(df)}")
            print("="*50)
            
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