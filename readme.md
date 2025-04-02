# Proyecto ETL: Carga, Relación y Reporte de Datos
Este proyecto simula un flujo ETL (Extract, Transform, Load) automatizado para procesar datos de ventas, generando reportes analíticos y enviándolos por correo electrónico.

## Descripción General
El sistema realiza las siguientes operaciones principales:

Carga de datos desde Excel a PostgreSQL: Lee un archivo Excel con múltiples hojas (clientes, productos, ventas) y los carga a una base de datos PostgreSQL.

Generación de reportes analíticos: Consulta los datos cargados, realiza análisis y genera reportes en diferentes formatos.

Distribución automática: Envía los reportes por correo electrónico con métricas resumidas.

# Características Principales
ETL automatizado: Proceso completo de extracción, transformación y carga de datos

Múltiples formatos de salida: Reportes en Excel, CSV y consola

Notificación por email: Envío automático con adjuntos y resumen

Manejo excelente de errores: Sistema de reintentos y logging detallado

Configuración modular: Credenciales y parámetros en archivos separados

## Componentes del Sistema
1. Script de Carga de Datos (cargar_datos.py)
Verifica la estructura del archivo Excel de entrada

Crea tablas en PostgreSQL si no existen

Inserta o actualiza datos manteniendo la información existente

Proporciona feedback detallado del proceso


2. Generador de Reportes (reporte_ventas.py)
Consulta las ventas con información de clientes y productos

Filtra por rango de fechas automáticamente detectado

Calcula métricas clave:

Total facturado

Producto más vendido (por monto)

Cliente que más compró

Genera archivo Excel con un formato establecido

Envía email con adjunto y resumen

3. Generador de envios de Email(envio_email.py)
Configuración SMTP para distribución masiva

Reportes en Excel/CSV con formato optimizado

Métricas clave listas para presentación que seria el resumen del cuerpo

3 intentos ante fallos de conexión en caso de no haberse enviado correctamente 
## Librerías principales:

- pandas

- SQLAlchemy

- openpyxl

- psycopg2 (PostgreSQL adapter)

- smtplib (para envío de emails)

## Librerias No tan principales

- loggin

- os

- sys

- pathlib

- datetime

- email.mine

# Configuración
 - Base de datos: Editar config/database.py con las credenciales de PostgreSQL

 - Email: Configurar parámetros SMTP en config/email.py

 - Archivo de datos: Colocar el Excel fuente en data/input/datos_fuente.xlsx

# Estructura del Proyecto
#### ETL_Ventas/
#### │
#### ├── config/                   # Configuraciones del sistema
#### │   ├── database.py           # Conexión a PostgreSQL
#### │   ├── email.py              # Configuración SMTP para envíos
#### │   └── config.ini            # Parámetros globales
#### │
#### ├── data/                     # Gestión de archivos de datos
#### │   ├── input/                # Datos fuente (Excel/CSV)
#### │   └── output/               # Reportes generados
#### │
#### ├── scripts/                  # Lógica principal del ETL
#### │   ├── cargar_datos.py       # Extracción y carga a PostgreSQL
#### │   ├── reporte_ventas.py     # Generación de reportes analíticos
#### │   ├── envio_email.py        # Distribución automática por email
#### │   └── script.py             # Orquestador del flujo completo
#### │
#### ├── sql/                      # Consultas y estructura de base de datos
#### │   ├── tablas.sql            # Esquema de la base de datos (DDL)
#### │   └── query.sql             # Consultas frecuentes (DML)
#### │
#### ├── logs/                     # Registros de ejecución
#### │   └── ejecucion_YYYYMMDD.log
#### │
#### ├── .gitignore                # Archivos excluidos de control de versiones
#### ├── requirements.txt          # Dependencias del proyecto
#### └── README.md                 # Documentación principal

# Ejecución en orden

1. Cargar datos iniciales:
python scripts/cargar_datos.py

2. Generar y enviar reporte:
python scripts/reporte_ventas.py

3. Cargar y enviar al Email:
python scripts/python/envio_email.py

# Ejecucion directa: # Realiza directamente la ejecucion total del programa
python scripts/python/script.py

# Logging

El sistema registra todos los eventos importantes en consola, incluyendo:

Conexiones exitosas o fallidas

Progreso de carga de datos

Generación de reportes

Intentos de envio de email


# Personalización
Los scripts estan preparados y pueden adaptarse para:

- Diferentes estructuras de Excel

- Otras bases de datos SQL

- Distintos formatos de reporte

- Formas alternatvias de distribución    