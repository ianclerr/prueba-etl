-- Consulta principal con JOINs
SELECT 
    v.venta_id,
    c.nombre AS cliente,
    p.nombre AS producto,
    p.categoria,
    v.fecha,
    v.cantidad,
    p.precio AS precio_unitario,
    v.monto_total,
    (v.cantidad * p.precio) AS total_calculado
FROM 
    ventas v
INNER JOIN clientes c ON v.cliente_id = c.cliente_id
INNER JOIN productos p ON v.producto_id = p.producto_id
WHERE 
    v.fecha BETWEEN '2023-01-01' AND '2023-12-31';

-- Consulta adicional: Resumen analítico
SELECT 
    p.categoria,
    SUM(v.monto_total) AS total_ventas,
    COUNT(*) AS total_transacciones,
    ROUND(AVG(v.monto_total), 2) AS promedio_venta
FROM 
    ventas v
JOIN productos p ON v.producto_id = p.producto_id
GROUP BY p.categoria
ORDER BY total_ventas DESC;

-- Estos son ""ejemplos"" de consultas un poco mas complejas que se utilizan en el codigo
-- utilizando JOIN - GROUP BY - ORDER BY - BETWEEN