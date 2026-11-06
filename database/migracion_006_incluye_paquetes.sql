-- Migración 006: lo que incluye cada paquete se elige en el formulario
-- {"tipos": ["alojamiento", "transporte", ...], "otros": ["Cena de bienvenida", ...]}
USE travelers_db;

ALTER TABLE paquetes_turisticos
    ADD COLUMN incluye JSON NULL;
