DROP DATABASE IF EXISTS travelers_db;

CREATE DATABASE travelers_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE travelers_db;

-- =====================================================
-- TABLA: roles
-- =====================================================
CREATE TABLE roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(45) NOT NULL UNIQUE
);

-- =====================================================
-- TABLA: funcionalidades
-- =====================================================
CREATE TABLE funcionalidades (
    id_funcionalidad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(45) NOT NULL UNIQUE
);

-- =====================================================
-- TABLA: ciudades
-- =====================================================
CREATE TABLE ciudades (
    id_ciudad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(45) NOT NULL,
    departamento VARCHAR(45) NOT NULL,
    pais VARCHAR(45) NOT NULL,

    UNIQUE (nombre, departamento, pais)
);

-- =====================================================
-- TABLA: usuarios
-- =====================================================
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    contrasena_hash VARCHAR(255) NOT NULL,
    estado VARCHAR(45) NOT NULL DEFAULT 'activo',
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verificacion_email VARCHAR(45) NOT NULL DEFAULT 'pendiente',
    rol_id INT NOT NULL,
    -- Cuenta de Google vinculada (claim "sub") y si el usuario tiene contraseña propia
    google_sub VARCHAR(255) NULL,
    tiene_contrasena TINYINT(1) NOT NULL DEFAULT 1,
    -- Foto de perfil: /uploads/avatars/... o URL de la foto de Google
    foto_url VARCHAR(500) NULL,

    CONSTRAINT uq_usuarios_google_sub
        UNIQUE (google_sub),

    CONSTRAINT fk_usuarios_roles
        FOREIGN KEY (rol_id)
        REFERENCES roles(id_rol)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- =====================================================
-- TABLA INTERMEDIA: roles_has_funcionalidades
-- =====================================================
CREATE TABLE roles_has_funcionalidades (
    roles_id_rol INT NOT NULL,
    funcionalidades_id_funcionalidad INT NOT NULL,

    PRIMARY KEY (roles_id_rol, funcionalidades_id_funcionalidad),

    CONSTRAINT fk_roles_funcionalidades_roles
        FOREIGN KEY (roles_id_rol)
        REFERENCES roles(id_rol)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_roles_funcionalidades_funcionalidades
        FOREIGN KEY (funcionalidades_id_funcionalidad)
        REFERENCES funcionalidades(id_funcionalidad)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- =====================================================
-- TABLA: clientes
-- =====================================================
CREATE TABLE clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    identificacion VARCHAR(30) NOT NULL UNIQUE,
    fecha_nacimiento DATE NOT NULL,
    ciudad_id INT NOT NULL,

    CONSTRAINT fk_clientes_usuarios
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_clientes_ciudades
        FOREIGN KEY (ciudad_id)
        REFERENCES ciudades(id_ciudad)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- =====================================================
-- TABLA: proveedores
-- =====================================================
CREATE TABLE proveedores (
    id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    rut VARCHAR(30) NOT NULL UNIQUE,
    telefono VARCHAR(30) NOT NULL,
    direccion VARCHAR(45) NOT NULL,
    nombre_empresa VARCHAR(100) NOT NULL,
    fecha_verificacion DATETIME NULL,
    fecha_solicitud DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_verificacion VARCHAR(45) NOT NULL DEFAULT 'pendiente',
    ciudad_id INT NOT NULL,
    -- Cuenta donde la agencia le paga al proveedor
    banco VARCHAR(60) NULL,
    tipo_cuenta VARCHAR(20) NULL,
    numero_cuenta VARCHAR(30) NULL,
    titular_cuenta VARCHAR(100) NULL,

    CONSTRAINT fk_proveedores_usuarios
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_proveedores_ciudades
        FOREIGN KEY (ciudad_id)
        REFERENCES ciudades(id_ciudad)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- =====================================================
-- TABLA: productos
-- =====================================================
CREATE TABLE productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    ciudad_id INT NOT NULL,
    descripcion MEDIUMTEXT NOT NULL,
    proveedor_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    tipo_producto VARCHAR(45) NOT NULL,
    estado VARCHAR(45) NOT NULL DEFAULT 'activo',
    costo DECIMAL(10,2) NOT NULL,
    -- persona | noche | dia | servicio
    unidad_cobro VARCHAR(20) NOT NULL DEFAULT 'persona',

    CONSTRAINT fk_productos_ciudades
        FOREIGN KEY (ciudad_id)
        REFERENCES ciudades(id_ciudad)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_productos_proveedores
        FOREIGN KEY (proveedor_id)
        REFERENCES proveedores(id_proveedor)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- =====================================================
-- TABLA: paquetes_turisticos
-- =====================================================
CREATE TABLE paquetes_turisticos (
    id_paquete_turistico INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion MEDIUMTEXT NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    descuento INT NOT NULL DEFAULT 0,
    estado VARCHAR(35) NOT NULL DEFAULT 'activo',
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    cupo_max INT NOT NULL,
    ciudades_id_ciudad INT NOT NULL,

    CONSTRAINT fk_paquetes_ciudades
        FOREIGN KEY (ciudades_id_ciudad)
        REFERENCES ciudades(id_ciudad)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- =====================================================
-- TABLA INTERMEDIA: paquetes_turisticos_has_productos
-- =====================================================
CREATE TABLE paquetes_turisticos_has_productos (
    paquetes_turisticos_id_paquete_turistico INT NOT NULL,
    productos_id_producto INT NOT NULL,
    cantidad INT NOT NULL DEFAULT 1,

    PRIMARY KEY (
        paquetes_turisticos_id_paquete_turistico,
        productos_id_producto
    ),

    CONSTRAINT fk_paquetes_productos_paquetes
        FOREIGN KEY (paquetes_turisticos_id_paquete_turistico)
        REFERENCES paquetes_turisticos(id_paquete_turistico)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_paquetes_productos_productos
        FOREIGN KEY (productos_id_producto)
        REFERENCES productos(id_producto)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- =====================================================
-- TABLA: reservas
-- =====================================================
CREATE TABLE reservas (
    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    fecha_compra DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_reserva DATE NOT NULL,
    cantidad_personas INT NOT NULL DEFAULT 1,
    cliente_id INT NOT NULL,
    id_paquete_turistico INT NOT NULL,
    total_reserva DECIMAL(10,2) NOT NULL,
    estado VARCHAR(45) NOT NULL DEFAULT 'pendiente',
    codigo_reserva VARCHAR(45) NOT NULL UNIQUE,
    -- Cancelación por parte del cliente
    fecha_cancelacion DATETIME NULL,
    penalidad_cancelacion DECIMAL(10,2) NULL,
    reembolso DECIMAL(10,2) NULL,

    CONSTRAINT fk_reservas_clientes
        FOREIGN KEY (cliente_id)
        REFERENCES clientes(id_cliente)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_reservas_paquetes
        FOREIGN KEY (id_paquete_turistico)
        REFERENCES paquetes_turisticos(id_paquete_turistico)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- =====================================================
-- TABLA: acompanantes
-- =====================================================
CREATE TABLE acompanantes (
    id_acompanante INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    documento VARCHAR(45) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    reserva_id INT NOT NULL,

    CONSTRAINT fk_acompanantes_reservas
        FOREIGN KEY (reserva_id)
        REFERENCES reservas(id_reserva)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- =====================================================
-- TABLA: pagos
-- =====================================================
CREATE TABLE pagos (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    metodo_pago VARCHAR(45) NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    estado_pago VARCHAR(45) NOT NULL DEFAULT 'pendiente',
    fecha_pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    referencia_pago VARCHAR(45) NOT NULL UNIQUE,
    reserva_id INT NOT NULL UNIQUE,

    CONSTRAINT fk_pagos_reservas
        FOREIGN KEY (reserva_id)
        REFERENCES reservas(id_reserva)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- =====================================================
-- TABLA: notificacion_email
-- =====================================================
CREATE TABLE notificacion_email (
    id_notificacion_email INT AUTO_INCREMENT PRIMARY KEY,
    destinatario VARCHAR(100) NOT NULL,
    asunto VARCHAR(100) NOT NULL,
    mensaje MEDIUMTEXT NOT NULL,
    tipo_notificacion VARCHAR(45) NOT NULL,
    estado_envio VARCHAR(45) NOT NULL DEFAULT 'pendiente',
    fecha_envio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuarios_id_usuario INT NOT NULL,
    reservas_id_reserva INT NULL,

    CONSTRAINT fk_notificacion_usuarios
        FOREIGN KEY (usuarios_id_usuario)
        REFERENCES usuarios(id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_notificacion_reservas
        FOREIGN KEY (reservas_id_reserva)
        REFERENCES reservas(id_reserva)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- =====================================================
-- TABLA: imagenes_paquetes
-- Las imágenes viven en S3 y se sirven por CloudFront.
-- s3_key debe tener el formato "<id_paquete>/<archivo>".
-- =====================================================
CREATE TABLE imagenes_paquetes (
    id_imagen INT AUTO_INCREMENT PRIMARY KEY,
    paquete_id INT NOT NULL,
    s3_key VARCHAR(500) NOT NULL,
    es_portada TINYINT(1) NOT NULL DEFAULT 0,
    orden INT NOT NULL DEFAULT 0,

    CONSTRAINT uq_imagen_paquete
        UNIQUE (paquete_id, s3_key),

    CONSTRAINT fk_imagen_paquete
        FOREIGN KEY (paquete_id)
        REFERENCES paquetes_turisticos(id_paquete_turistico)
        ON DELETE CASCADE
);

-- =====================================================
-- TABLAS: órdenes de pago a proveedores y configuración
-- =====================================================
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

-- =====================================================
-- DATOS INICIALES: roles
-- =====================================================
INSERT INTO roles (descripcion) VALUES
('administrador'),
('cliente'),
('proveedor');

-- =====================================================
-- DATOS INICIALES: funcionalidades
-- =====================================================
INSERT INTO funcionalidades (nombre) VALUES
('gestionar_usuarios'),
('gestionar_proveedores'),
('gestionar_productos'),
('gestionar_paquetes'),
('gestionar_reservas'),
('gestionar_pagos'),
('comprar_paquetes'),
('consultar_paquetes'),
('registrar_cliente'),
('registrar_proveedor'),
('verificar_proveedor'),
('enviar_notificaciones');

-- =====================================================
-- DATOS INICIALES: roles_has_funcionalidades
-- =====================================================

-- Administrador
INSERT INTO roles_has_funcionalidades 
(roles_id_rol, funcionalidades_id_funcionalidad)
VALUES
(1, 1),
(1, 2),
(1, 3),
(1, 4),
(1, 5),
(1, 6),
(1, 8),
(1, 11),
(1, 12);

-- Cliente
INSERT INTO roles_has_funcionalidades 
(roles_id_rol, funcionalidades_id_funcionalidad)
VALUES
(2, 7),
(2, 8),
(2, 9),
(2, 12);

-- Proveedor
INSERT INTO roles_has_funcionalidades 
(roles_id_rol, funcionalidades_id_funcionalidad)
VALUES
(3, 3),
(3, 8),
(3, 10),
(3, 12);

-- =====================================================
-- DATOS INICIALES: ciudades
-- =====================================================
INSERT INTO ciudades (nombre, departamento, pais) VALUES
('Medellín', 'Antioquia', 'Colombia'),
('Bogotá', 'Cundinamarca', 'Colombia'),
('Cartagena', 'Bolívar', 'Colombia'),
('Santa Marta', 'Magdalena', 'Colombia'),
('San Andrés', 'San Andrés y Providencia', 'Colombia'),
('Salento', 'Quindío', 'Colombia'),
('Jardín', 'Antioquia', 'Colombia'),
('San Gil', 'Santander', 'Colombia'),
('Leticia', 'Amazonas', 'Colombia'),
('Villa de Leyva', 'Boyacá', 'Colombia');



-- =========================================================
-- Mejoras (equivale a migracion_005_mejoras.sql)
-- =========================================================

CREATE TABLE IF NOT EXISTS bitacora_admin (
    id_registro INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    usuario_nombre VARCHAR(100) NOT NULL,
    accion VARCHAR(60) NOT NULL,
    entidad VARCHAR(45) NOT NULL,
    entidad_id INT NULL,
    descripcion VARCHAR(255) NOT NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_bitacora_fecha (fecha),
    INDEX ix_bitacora_entidad (entidad),
    INDEX ix_bitacora_accion (accion),
    CONSTRAINT fk_bitacora_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id_usuario) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS notificaciones_app (
    id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo VARCHAR(40) NOT NULL,
    titulo VARCHAR(120) NOT NULL,
    mensaje VARCHAR(255) NOT NULL,
    enlace VARCHAR(255) NULL,
    leida TINYINT(1) NOT NULL DEFAULT 0,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_notif_usuario (usuario_id),
    INDEX ix_notif_fecha (fecha),
    CONSTRAINT fk_notif_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id_usuario) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS favoritos (
    id_favorito INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    paquete_id INT NOT NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_favorito_usuario_paquete (usuario_id, paquete_id),
    CONSTRAINT fk_favorito_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_favorito_paquete FOREIGN KEY (paquete_id)
        REFERENCES paquetes_turisticos (id_paquete_turistico) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cupones (
    id_cupon INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    descripcion VARCHAR(150) NULL,
    tipo VARCHAR(20) NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    usos_maximos INT NULL,
    usos INT NOT NULL DEFAULT 0,
    monto_minimo DECIMAL(10,2) NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'activo',
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resenas (
    id_resena INT AUTO_INCREMENT PRIMARY KEY,
    reserva_id INT NOT NULL UNIQUE,
    paquete_id INT NOT NULL,
    usuario_id INT NOT NULL,
    calificacion INT NOT NULL,
    comentario VARCHAR(600) NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'visible',
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_resena_paquete (paquete_id),
    CONSTRAINT fk_resena_reserva FOREIGN KEY (reserva_id)
        REFERENCES reservas (id_reserva) ON DELETE CASCADE,
    CONSTRAINT fk_resena_paquete FOREIGN KEY (paquete_id)
        REFERENCES paquetes_turisticos (id_paquete_turistico) ON DELETE CASCADE,
    CONSTRAINT fk_resena_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id_usuario) ON DELETE CASCADE
);

ALTER TABLE reservas
    ADD COLUMN cupon_id INT NULL,
    ADD COLUMN descuento_cupon DECIMAL(10,2) NULL,
    ADD COLUMN recordatorio_enviado DATETIME NULL,
    ADD CONSTRAINT fk_reserva_cupon FOREIGN KEY (cupon_id)
        REFERENCES cupones (id_cupon) ON DELETE SET NULL;

ALTER TABLE ciudades
    ADD COLUMN latitud DECIMAL(9,6) NULL,
    ADD COLUMN longitud DECIMAL(9,6) NULL;

-- Coordenadas de los destinos para el mapa de la portada
UPDATE ciudades SET latitud = 6.244203,  longitud = -75.581212 WHERE nombre = 'Medellín';
UPDATE ciudades SET latitud = 4.711000,  longitud = -74.072100 WHERE nombre = 'Bogotá';
UPDATE ciudades SET latitud = 10.391000, longitud = -75.479400 WHERE nombre = 'Cartagena';
UPDATE ciudades SET latitud = 11.240400, longitud = -74.199000 WHERE nombre = 'Santa Marta';
UPDATE ciudades SET latitud = 12.584700, longitud = -81.700600 WHERE nombre = 'San Andrés';
UPDATE ciudades SET latitud = 4.637600,  longitud = -75.570600 WHERE nombre = 'Salento';
UPDATE ciudades SET latitud = 5.598600,  longitud = -75.818900 WHERE nombre = 'Jardín';
UPDATE ciudades SET latitud = 6.555800,  longitud = -73.133900 WHERE nombre = 'San Gil';
UPDATE ciudades SET latitud = -4.215300, longitud = -69.940600 WHERE nombre = 'Leticia';
UPDATE ciudades SET latitud = 5.633600,  longitud = -73.525300 WHERE nombre = 'Villa de Leyva';
