import pandas as pd
from sqlalchemy import create_engine, text
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from datetime import datetime
from openpyxl import Workbook
import sys
from pathlib import Path
import time
import logging

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Importar configuraciones desde la carpeta config
sys.path.append(str(Path(__file__).parent.parent.parent))  # Añadir el directorio raíz al path

from config.database import get_db_uri
from config.email import EMAIL_CONFIG

def conectar_postgres():
    """
    Establece conexión con PostgreSQL
    
    Returns:
        engine: Objeto de conexión SQLAlchemy o None si falla
    """
    try:
        engine = create_engine(get_db_uri())
        logging.info("✅ Conexión exitosa a PostgreSQL")
        return engine
    except Exception as e:
        logging.error(f"❌ Error de conexión: {str(e)}")
        return None

def obtener_rango_fechas(engine):
    """
    Obtiene el rango real de fechas disponible en la base de datos
    
    Args:
        engine: Conexión a la base de datos
        
    Returns:
        tuple: (fecha_min, fecha_max) o None si hay error
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT MIN(fecha), MAX(fecha) FROM ventas"))
            return result.fetchone()
    except Exception as e:
        logging.error(f"❌ Error al obtener rango de fechas: {str(e)}")
        return None

def generar_reporte_excel(df, fecha_min, fecha_max):
    """
    Genera el archivo Excel con formato profesional
    
    Args:
        df: DataFrame con los datos a exportar
        fecha_min: Fecha inicial del reporte
        fecha_max: Fecha final del reporte
        
    Returns:
        str: Ruta del archivo generado o None si falla
    """
    try:
        os.makedirs('reportes', exist_ok=True)
        nombre_reporte = f"reportes/reporte_ventas_{fecha_min.strftime('%Y%m%d')}_{fecha_max.strftime('%Y%m%d')}.xlsx"
        
        with pd.ExcelWriter(nombre_reporte, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Ventas')
            
            workbook = writer.book
            worksheet = writer.sheets['Ventas']
            
            # Formatear columnas
            for cell in worksheet['B'][1:]:
                cell.number_format = 'DD/MM/YYYY'
            
            column_widths = {'A': 10, 'B': 12, 'C': 25, 'D': 25, 'E': 10, 'F': 18}
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            for cell in worksheet['F'][1:]:
                cell.number_format = '"Gs."#,##0'
        
        logging.info(f"📊 Reporte generado: {nombre_reporte}")
        return nombre_reporte
    except Exception as e:
        logging.error(f"❌ Error al generar Excel: {str(e)}")
        return None

def obtener_metricas_ventas(df):
    """
    Calcula las métricas clave del reporte
    
    Args:
        df: DataFrame con los datos de ventas
        
    Returns:
        dict: Diccionario con las métricas calculadas
    """
    return {
        'total': df['monto_total'].sum(),
        'producto_top': df.groupby('producto')['monto_total'].sum().idxmax(),
        'monto_producto': df.groupby('producto')['monto_total'].sum().max(),
        'cliente_top': df.groupby('cliente')['monto_total'].sum().idxmax(),
        'monto_cliente': df.groupby('cliente')['monto_total'].sum().max()
    }

def enviar_email_con_reintentos(reporte_path, metrics, fecha_min, fecha_max, total_registros, max_intentos=3):
    """
    Envía el email con el reporte, con reintentos automáticos en caso de fallo
    
    Args:
        reporte_path: Ruta del archivo a enviar
        metrics: Métricas calculadas del reporte
        fecha_min: Fecha inicial del reporte
        fecha_max: Fecha final del reporte
        total_registros: Total de registros procesados
        max_intentos: Número máximo de reintentos (default: 3)
        
    Returns:
        bool: True si el envío fue exitoso, False si falló después de todos los reintentos
    """
    intento = 1
    while intento <= max_intentos:
        try:
            logging.info(f"✉️ Procesando envío de email (Intento {intento}/{max_intentos})...")
            
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
                logging.info("✅ Email enviado exitosamente")
                return True
                
        except Exception as e:
            logging.error(f"❌ Error al enviar email (Intento {intento}): {str(e)}")
            if intento < max_intentos:
                logging.info(f"⏳ Reintentando en 5 segundos...")
                time.sleep(5)
            intento += 1
    
    logging.error(f"🚨 No se pudo enviar el email después de {max_intentos} intentos")
    return False

def main():
    """
    Función principal que orquesta todo el proceso:
    1. Conexión a la base de datos
    2. Obtención de datos
    3. Generación de reporte
    4. Envío de email con reintentos automáticos
    """
    logging.info("\n=== SISTEMA DE ENVÍO DE REPORTES ===")
    
    # Paso 1: Conexión a la base de datos
    engine = conectar_postgres()
    if not engine:
        return
    
    try:
        # Paso 2: Obtener rango de fechas
        fechas = obtener_rango_fechas(engine)
        if not fechas:
            return
        fecha_min, fecha_max = fechas
        logging.info(f"📅 Rango de fechas disponible: {fecha_min} a {fecha_max}")
        
        # Paso 3: Consultar datos
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
                logging.warning("⚠️ No hay ventas en el período disponible")
                return
            
            # Paso 4: Calcular métricas (aunque no se muestren)
            metrics = obtener_metricas_ventas(df)
            
            # Paso 5: Generar Excel
            reporte_path = generar_reporte_excel(df, fecha_min, fecha_max)
            if not reporte_path:
                return
            
            # Paso 6: Enviar email con reintentos
            enviar_email_con_reintentos(reporte_path, metrics, fecha_min, fecha_max, len(df))
            
    except Exception as e:
        logging.error(f"❌ Error inesperado: {str(e)}")
    finally:
        engine.dispose()
        logging.info("🔚 Proceso completado")

if __name__ == "__main__":
    main()