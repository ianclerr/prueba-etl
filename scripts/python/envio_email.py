import pandas as pd
from sqlalchemy import create_engine, text
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from datetime import datetime
from openpyxl import Workbook

# Configuración de PostgreSQL
DB_CONFIG = {
    "host": "localhost",
    "database": "test_etl",
    "user": "postgres",
    "password": "root",
    "port": "5432"
}

# Configuración de Email (usar contraseña de aplicación)
EMAIL_CONFIG = {
    'email_from': 'clerrenaud.ian@gmail.com',
    'email_password': 'tapwatxzsrhrrztx',
    'email_to': 'clerrenaud.ian@gmail.com',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

def conectar_postgres():
    """Establece conexión con PostgreSQL"""
    try:
        engine = create_engine(
            f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        print("✅ Conexión exitosa a PostgreSQL")
        return engine
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return None

def obtener_rango_fechas(engine):
    """Obtiene el rango real de fechas disponible en la base de datos"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MIN(fecha), MAX(fecha) FROM ventas"))
        return result.fetchone()

def mostrar_reporte_consola(metrics, fecha_min, fecha_max, total_registros):
    """Muestra el reporte formateado en la consola"""
    print("\n" + "="*50)
    print("REPORTE DE VENTAS - RESUMEN".center(50))
    print("="*50)
    print(f"\nFECHA GENERACIÓN: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"PERÍODO ANALIZADO: {fecha_min.strftime('%d/%m/%Y')} al {fecha_max.strftime('%d/%m/%Y')}")
    print("\nMÉTRICAS PRINCIPALES")
    print("-"*20)
    print(f"* TOTAL FACTURADO: Gs. {metrics['total']:,.0f}")
    print(f"* PRODUCTO DESTACADO: {metrics['producto_top']} (Gs. {metrics['monto_producto']:,.0f})")
    print(f"* CLIENTE DESTACADO: {metrics['cliente_top']} (Gs. {metrics['monto_cliente']:,.0f})")
    print("\n" + "="*50)
    print(f"TOTAL VENTAS ANALIZADAS: {total_registros}")
    print("="*50)

def generar_reporte_excel(df, fecha_min, fecha_max):
    """Genera el archivo Excel con formato profesional"""
    try:
        os.makedirs('reportes', exist_ok=True)
        nombre_reporte = f"reportes/reporte_ventas_{fecha_min.strftime('%Y%m%d')}_{fecha_max.strftime('%Y%m%d')}.xlsx"
        
        with pd.ExcelWriter(nombre_reporte, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Ventas')
            
            workbook = writer.book
            worksheet = writer.sheets['Ventas']
            
            # Formato de fechas
            for cell in worksheet['B'][1:]:
                cell.number_format = 'DD/MM/YYYY'
            
            # Ajustar anchos de columnas
            column_widths = {'A': 10, 'B': 12, 'C': 25, 'D': 25, 'E': 10, 'F': 18}
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            # Formato para montos
            for cell in worksheet['F'][1:]:
                cell.number_format = '"Gs."#,##0'
        
        return nombre_reporte
    except Exception as e:
        print(f"❌ Error al generar Excel: {str(e)}")
        return None

def obtener_metricas_ventas(df):
    """Calcula las métricas clave del reporte"""
    return {
        'total': df['monto_total'].sum(),
        'producto_top': df.groupby('producto')['monto_total'].sum().idxmax(),
        'monto_producto': df.groupby('producto')['monto_total'].sum().max(),
        'cliente_top': df.groupby('cliente')['monto_total'].sum().idxmax(),
        'monto_cliente': df.groupby('cliente')['monto_total'].sum().max()
    }

def enviar_email(reporte_path, metrics, fecha_min, fecha_max, total_registros):
    """Envía el email con el reporte"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['email_from']
        msg['To'] = EMAIL_CONFIG['email_to']
        msg['Subject'] = f"REPORTE VENTAS {fecha_min.strftime('%d-%m-%Y')} al {fecha_max.strftime('%d-%m-%Y')}"
        
        cuerpo = f"""
REPORTE DE VENTAS - RESUMEN
==========================

FECHA GENERACIÓN: {datetime.now().strftime('%d/%m/%Y %H:%M')}
PERÍODO ANALIZADO: {fecha_min.strftime('%d/%m/%Y')} al {fecha_max.strftime('%d/%m/%Y')}

MÉTRICAS PRINCIPALES
--------------------
* TOTAL FACTURADO: Gs. {metrics['total']:,.0f}
* PRODUCTO DESTACADO: {metrics['producto_top']} (Gs. {metrics['monto_producto']:,.0f})
* CLIENTE DESTACADO: {metrics['cliente_top']} (Gs. {metrics['monto_cliente']:,.0f})

TOTAL VENTAS ANALIZADAS: {total_registros}

Se adjunta el reporte detallado en formato Excel.
"""
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        with open(reporte_path, "rb") as f:
            adjunto = MIMEApplication(f.read(), _subtype="xlsx")
            adjunto.add_header('Content-Disposition', 'attachment', 
                             filename=f"reporte_ventas_{fecha_min.strftime('%Y%m%d')}_{fecha_max.strftime('%Y%m%d')}.xlsx")
            msg.attach(adjunto)
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['email_from'], EMAIL_CONFIG['email_password'])
            server.send_message(msg)
            print("✅ Email enviado exitosamente")
            
    except Exception as e:
        print(f"❌ Error al enviar email: {str(e)}")

def main():
    print("\n=== SISTEMA DE REPORTES DE VENTAS ===")
    
    engine = conectar_postgres()
    if not engine:
        return
    
    try:
        # Obtener fechas reales de la base de datos
        fecha_min, fecha_max = obtener_rango_fechas(engine)
        print(f"\nℹ️ Rango de fechas disponible: {fecha_min} a {fecha_max}")
        
        # Consultar datos para el rango disponible
        query = text("""
        SELECT 
            v.venta_id,
            v.fecha,
            c.nombre AS cliente,
            p.nombre AS producto,
            v.cantidad,
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
                print("⚠️ No hay ventas en el período disponible")
                return
            
            # Calcular métricas
            metrics = obtener_metricas_ventas(df)
            
            # Mostrar reporte en consola
            mostrar_reporte_consola(metrics, fecha_min, fecha_max, len(df))
            
            # Generar Excel
            reporte_path = generar_reporte_excel(df, fecha_min, fecha_max)
            if not reporte_path:
                return
            
            # Enviar email
            enviar_email(reporte_path, metrics, fecha_min, fecha_max, len(df))
            
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()