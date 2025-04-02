"""
SCRIPT DE GENERACIÓN Y ENVÍO DE REPORTES DE VENTAS DESDE POSTGRESQL

Este script automatiza:
1. Extracción de datos de ventas desde PostgreSQL
2. Generación de reporte en Excel con formato profesional
3. Envío por email con métricas resumidas y archivo adjunto
4. Manejo de errores y reintentos automáticos

Configuración requerida:
- Credenciales de DB en config/database.py
- Configuración de email en config/email.py
"""
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

# ==============================================
# CONFIGURACIÓN INICIAL
# ==============================================

# Configuración del sistema de logging (registro de eventos)
logging.basicConfig(
    level=logging.INFO,  # Nivel de detalle (INFO, WARNING, ERROR)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del mensaje
    handlers=[logging.StreamHandler()]  # Mostrar en consola
)

# Añadir ruta del proyecto para importar configuraciones
sys.path.append(str(Path(__file__).parent.parent.parent))

# Importar configuraciones externas
from config.database import get_db_uri  # Credenciales de DB
from config.email import EMAIL_CONFIG  # Configuración de email

# ==============================================
# FUNCIONES PRINCIPALES
# ==============================================

def conectar_postgres():
    """
    Establece conexión con la base de datos PostgreSQL
    
    Returns:
        engine: Objeto de conexión SQLAlchemy o None si falla
    """
    try:
        # Crear motor de conexión usando la URI de la DB
        engine = create_engine(get_db_uri())
        logging.info("✅ Conexión exitosa a PostgreSQL")
        return engine
    except Exception as e:
        logging.error(f"❌ Error de conexión: {str(e)}")
        return None

def obtener_rango_fechas(engine):
    """
    Obtiene el rango de fechas disponible en la tabla de ventas
    
    Args:
        engine: Conexión activa a la base de datos
        
    Returns:
        tuple: (fecha_min, fecha_max) o None si hay error
    """
    try:
        with engine.connect() as conn:
            # Consulta SQL para obtener fechas mínima y máxima
            result = conn.execute(text("SELECT MIN(fecha), MAX(fecha) FROM ventas"))
            return result.fetchone()
    except Exception as e:
        logging.error(f"❌ Error al obtener rango de fechas: {str(e)}")
        return None

def generar_reporte_excel(df, fecha_min, fecha_max):
    """
    Genera archivo Excel con formato profesional a partir de los datos
    
    Args:
        df: DataFrame con los datos de ventas
        fecha_min: Fecha inicial del período
        fecha_max: Fecha final del período
        
    Returns:
        str: Ruta del archivo generado o None si falla
    """
    try:
        # Crear directorio para reportes si no existe
        os.makedirs('reportes', exist_ok=True)
        
        # Nombre del archivo con rango de fechas
        nombre_reporte = f"reportes/reporte_ventas_{fecha_min.strftime('%Y%m%d')}_{fecha_max.strftime('%Y%m%d')}.xlsx"
        
        # Crear archivo Excel con pandas y openpyxl
        with pd.ExcelWriter(nombre_reporte, engine='openpyxl') as writer:
            # Exportar DataFrame a Excel
            df.to_excel(writer, index=False, sheet_name='Ventas')
            
            # Obtener objetos para formateo
            workbook = writer.book
            worksheet = writer.sheets['Ventas']
            
            # Formatear columna de fechas
            for cell in worksheet['B'][1:]:
                cell.number_format = 'DD/MM/YYYY'
            
            # Ajustar anchos de columnas
            column_widths = {'A': 10, 'B': 12, 'C': 25, 'D': 25, 'E': 10, 'F': 18}
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            # Formatear columna de montos (moneda)
            for cell in worksheet['F'][1:]:
                cell.number_format = '"Gs."#,##0'
        
        logging.info(f"📊 Reporte generado: {nombre_reporte}")
        return nombre_reporte
    except Exception as e:
        logging.error(f"❌ Error al generar Excel: {str(e)}")
        return None

def obtener_metricas_ventas(df):
    """
    Calcula métricas clave a partir de los datos de ventas
    
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
    Envía email con reporte adjunto y sistema de reintentos
    
    Args:
        reporte_path: Ruta del archivo a adjuntar
        metrics: Métricas calculadas
        fecha_min: Fecha inicio del reporte
        fecha_max: Fecha fin del reporte
        total_registros: Total de ventas procesadas
        max_intentos: Intentos máximos de envío
        
    Returns:
        bool: True si tuvo éxito, False si falló
    """
    intento = 1
    while intento <= max_intentos:
        try:
            logging.info(f"✉️ Procesando envío de email (Intento {intento}/{max_intentos})...")
            
            # 1. CONFIGURAR MENSAJE MIME
            msg = MIMEMultipart()
            msg['From'] = EMAIL_CONFIG['email_from']
            msg['To'] = EMAIL_CONFIG['email_to']
            msg['Subject'] = f"REPORTE VENTAS {fecha_min.strftime('%d-%m-%Y')} al {fecha_max.strftime('%d-%m-%Y')}"
            
            # 2. CREAR CUERPO DEL EMAIL
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
            
            # 3. ADJUNTAR ARCHIVO EXCEL
            with open(reporte_path, "rb") as f:
                adjunto = MIMEApplication(f.read(), _subtype="xlsx")
                adjunto.add_header('Content-Disposition', 'attachment', 
                                filename=f"reporte_ventas_{fecha_min.strftime('%Y%m%d')}_{fecha_max.strftime('%Y%m%d')}.xlsx")
                msg.attach(adjunto)
            
            # 4. ENVIAR EMAIL POR SMTP
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.starttls()  # Seguridad TLS
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

# ==============================================
# FUNCIÓN PRINCIPAL
# ==============================================

def main():
    """
    Función principal que coordina todo el proceso:
    1. Conexión a DB
    2. Extracción de datos
    3. Generación de reporte
    4. Envío por email
    """
    logging.info("\n=== SISTEMA DE ENVÍO DE REPORTES ===")
    
    # 1. CONEXIÓN A LA BASE DE DATOS
    engine = conectar_postgres()
    if not engine:
        return
    
    try:
        # 2. OBTENER RANGO DE FECHAS
        fechas = obtener_rango_fechas(engine)
        if not fechas:
            return
        fecha_min, fecha_max = fechas
        logging.info(f"📅 Rango de fechas disponible: {fecha_min} a {fecha_max}")
        
        # 3. CONSULTAR DATOS DE VENTAS
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
            
            # 4. CALCULAR MÉTRICAS
            metrics = obtener_metricas_ventas(df)
            
            # 5. GENERAR REPORTE EXCEL
            reporte_path = generar_reporte_excel(df, fecha_min, fecha_max)
            if not reporte_path:
                return
            
            # 6. ENVIAR EMAIL CON REPORTE
            enviar_email_con_reintentos(reporte_path, metrics, fecha_min, fecha_max, len(df))
            
    except Exception as e:
        logging.error(f"❌ Error inesperado: {str(e)}")
    finally:
        engine.dispose()
        logging.info("🔚 Proceso completado")

# Punto de entrada del script
if __name__ == "__main__":
    main()