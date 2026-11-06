-- Migración 005: reseñas, favoritos, cupones, notificaciones en la app,
-- bitácora de administradores, recordatorios y coordenadas de ciudades.
USE travelers_db;

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
