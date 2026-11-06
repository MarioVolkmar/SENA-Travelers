-- =====================================================
-- Migración 002: foto de perfil y cancelación de reservas con penalidad
-- Para bases creadas antes de este cambio (script_BD_Travelers.sql ya lo incluye).
-- Solo agrega columnas que aceptan NULL; no modifica ni borra datos.
-- =====================================================
USE travelers_db;

ALTER TABLE usuarios
    ADD COLUMN foto_url VARCHAR(500) NULL;

ALTER TABLE reservas
    ADD COLUMN fecha_cancelacion DATETIME NULL,
    ADD COLUMN penalidad_cancelacion DECIMAL(10,2) NULL,
    ADD COLUMN reembolso DECIMAL(10,2) NULL;

-- Para revertir:
-- ALTER TABLE usuarios DROP COLUMN foto_url;
-- ALTER TABLE reservas DROP COLUMN fecha_cancelacion, DROP COLUMN penalidad_cancelacion, DROP COLUMN reembolso;
