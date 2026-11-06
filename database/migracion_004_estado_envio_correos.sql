-- Migración 004: los correos ya se envían de verdad por SMTP.
-- El estado "enviado_simulado" pasa a "enviado".
-- Estados posibles: pendiente, enviado, fallido, desactivado (EMAILS_ENABLED=false).
USE travelers_db;

UPDATE notificacion_email
SET estado_envio = 'enviado'
WHERE estado_envio = 'enviado_simulado';
