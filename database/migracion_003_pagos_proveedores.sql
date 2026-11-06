-- =====================================================
-- Migración 003: órdenes de pago a proveedores, configuración,
-- unidad de cobro de productos y datos bancarios de proveedores.
-- Para bases creadas antes de este cambio (script_BD_Travelers.sql ya lo incluye).
-- Solo agrega columnas y tablas; no modifica ni borra datos existentes.
-- =====================================================
USE travelers_db;

ALTER TABLE productos
    ADD COLUMN unidad_cobro VARCHAR(20) NOT NULL DEFAULT 'persona';

ALTER TABLE proveedores
    ADD COLUMN banco VARCHAR(60) NULL,
    ADD COLUMN tipo_cuenta VARCHAR(20) NULL,
    ADD COLUMN numero_cuenta VARCHAR(30) NULL,
    ADD COLUMN titular_cuenta VARCHAR(100) NULL;

CREATE TABLE ordenes_pago_proveedor (
    id_orden INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    proveedor_id INT NOT NULL,
    reserva_id INT NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento DATE NOT NULL,
    fecha_pago DATETIME NULL,
    referencia_pago VARCHAR(60) NULL,
    nota VARCHAR(255) NULL,

    CONSTRAINT uq_orden_proveedor_reserva UNIQUE (proveedor_id, reserva_id),
    CONSTRAINT fk_orden_proveedor FOREIGN KEY (proveedor_id) REFERENCES proveedores(id_proveedor),
    CONSTRAINT fk_orden_reserva FOREIGN KEY (reserva_id) REFERENCES reservas(id_reserva)
);

CREATE TABLE ordenes_pago_detalle (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    orden_id INT NOT NULL,
    producto_id INT NOT NULL,
    descripcion VARCHAR(150) NOT NULL,
    unidad_cobro VARCHAR(20) NOT NULL,
    cantidad INT NOT NULL,
    viajeros INT NOT NULL,
    costo_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_detalle_orden FOREIGN KEY (orden_id) REFERENCES ordenes_pago_proveedor(id_orden) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_producto FOREIGN KEY (producto_id) REFERENCES productos(id_producto)
);

CREATE TABLE configuraciones (
    clave VARCHAR(60) PRIMARY KEY,
    valor VARCHAR(255) NOT NULL
);

INSERT INTO configuraciones (clave, valor) VALUES ('dias_pago_proveedores', '15');

-- Hospedaje se cobra por noche y alimentación por día
UPDATE productos SET unidad_cobro = 'noche' WHERE tipo_producto = 'hospedaje';
UPDATE productos SET unidad_cobro = 'dia' WHERE tipo_producto = 'alimentacion';
