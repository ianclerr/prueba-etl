import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# Configuración de conexión
DB_CONFIG = {
    "host": "localhost",
    "database": "test_etl",
    "user": "postgres",
    "password": "root",
    "port": "5432"
}

def obtener_rango_fechas(engine):
    """Obtiene el rango real de fechas disponible en la base de datos"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MIN(fecha), MAX(fecha) FROM ventas"))
        return result.fetchone()

def generar_reporte_consola():
    """Genera y muestra el reporte directamente en la consola"""
    try:
        engine = create_engine(
            f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        
        # Obtener fechas reales
        fecha_min, fecha_max = obtener_rango_fechas(engine)
        
        # Consulta para obtener datos
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
            
            # Calcular métricas
            total_facturado = df['monto_total'].sum()
            producto_top = df.groupby('producto')['monto_total'].sum().idxmax()
            monto_producto = df.groupby('producto')['monto_total'].sum().max()
            cliente_top = df.groupby('cliente')['monto_total'].sum().idxmax()
            monto_cliente = df.groupby('cliente')['monto_total'].sum().max()
            
            # Mostrar reporte en consola
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

if __name__ == "__main__":
    print("\n" + "="*50)
    print("SISTEMA DE REPORTES DE VENTAS".center(50))
    print("="*50)
    generar_reporte_consola()