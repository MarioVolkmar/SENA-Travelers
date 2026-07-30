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
('San Andrés', 'San Andrés y Providencia', 'Colombia');

