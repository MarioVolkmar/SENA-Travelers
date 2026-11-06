-- =====================================================
-- Migración 001: inicio de sesión con Google
-- Para bases creadas antes de este cambio (script_BD_Travelers.sql ya lo incluye).
-- Solo agrega columnas; no modifica ni borra datos.
-- =====================================================
USE travelers_db;

ALTER TABLE usuarios
    ADD COLUMN google_sub VARCHAR(255) NULL,
    ADD CONSTRAINT uq_usuarios_google_sub UNIQUE (google_sub);

ALTER TABLE usuarios
    ADD COLUMN tiene_contrasena TINYINT(1) NOT NULL DEFAULT 1;

-- Para revertir:
-- ALTER TABLE usuarios DROP INDEX uq_usuarios_google_sub, DROP COLUMN google_sub, DROP COLUMN tiene_contrasena;
