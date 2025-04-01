-- Tabla clientes
CREATE TABLE IF NOT EXISTS clientes (
    cliente_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    direccion TEXT
);

-- Tabla productos
CREATE TABLE IF NOT EXISTS productos (
    producto_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    categoria VARCHAR(50)
);

-- Tabla ventas (con claves foráneas)
CREATE TABLE IF NOT EXISTS ventas (
    venta_id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(cliente_id),
    producto_id INTEGER REFERENCES productos(producto_id),
    fecha DATE NOT NULL,
    cantidad INTEGER NOT NULL,
    monto_total DECIMAL(12,2) NOT NULL
);