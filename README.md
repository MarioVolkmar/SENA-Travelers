# SENA-Travelers
Proyecto Técnico en Programación de Software 2026


# Travelers

Travelers es una plataforma web para una agencia turística, desarrollada como proyecto académico del programa Técnico en Programación de Software del SENA.

El sistema permite gestionar paquetes turísticos, clientes, proveedores, productos, reservas, pagos simulados y notificaciones por correo electrónico.

---

## Objetivo del proyecto

Desarrollar una aplicación web para una agencia turística que permita comercializar paquetes turísticos, administrar la información principal del negocio y facilitar el proceso de reserva y compra simulada por parte de los clientes.

El proyecto busca integrar una base de datos en MySQL, un backend en Python y una interfaz web en React, aplicando buenas prácticas de organización, control de versiones y programación orientada a objetos.

---

## Funciones principales del sistema

### Gestión de usuarios

El sistema permite manejar usuarios con diferentes roles dentro de la plataforma.

Roles principales:

- Administrador.
- Cliente.
- Proveedor.

Cada usuario cuenta con información básica como nombre, correo electrónico, contraseña protegida, estado y rol asignado.

---

### Gestión de clientes

El sistema permite registrar clientes para que puedan acceder a la plataforma, consultar paquetes turísticos, realizar reservas y simular compras.

Funciones relacionadas:

- Registro de clientes.
- Asociación del cliente con un usuario del sistema.
- Consulta de paquetes turísticos.
- Creación de reservas.
- Compra simulada de paquetes.
- Correos reales por SMTP (`EMAILS_ENABLED=true`). Cada correo queda registrado con estado `enviado`, `fallido` o `desactivado` (cuando `EMAILS_ENABLED=false`).

---

### Gestión de proveedores

El sistema permite que los proveedores se registren en la plataforma.

Antes de quedar habilitados, los proveedores deben ser verificados por un administrador.

Funciones relacionadas:

- Registro de proveedores.
- Registro de datos de empresa.
- Estado de verificación del proveedor.
- Aprobación o rechazo por parte del administrador.
- Asociación de proveedores con productos turísticos.

---

### Gestión de productos turísticos

Los productos turísticos representan servicios individuales que pueden formar parte de un paquete turístico.

Ejemplos de productos turísticos:

- Hospedaje.
- Transporte.
- Alimentación.
- Tours.
- Actividades.
- Guías turísticos.
- Seguros.

Funciones relacionadas:

- Crear productos turísticos.
- Consultar productos.
- Asociar productos a proveedores.
- Relacionar productos con paquetes turísticos.

---

### Gestión de paquetes turísticos

Los paquetes turísticos son los productos comerciales principales de la agencia.

Un paquete puede estar compuesto por varios productos turísticos.

Funciones relacionadas:

- Crear paquetes turísticos.
- Consultar paquetes disponibles.
- Asociar productos a paquetes.
- Definir precio, descuento, fechas, cupo y ciudad destino.
- Activar o desactivar paquetes.

---

### Gestión de reservas

El sistema permite que los clientes realicen reservas sobre paquetes turísticos.

Cada reserva contiene información como cliente, paquete, cantidad de personas, fecha, total y estado.

Funciones relacionadas:

- Crear reservas.
- Generar código único de reserva.
- Consultar reservas.
- Cambiar estado de reserva.
- Asociar acompañantes a una reserva.

---

### Gestión de pagos simulados

La primera versión del sistema no procesa dinero real.

Los pagos son simulados y se registran en la base de datos para representar el flujo funcional de compra.

Funciones relacionadas:

- Registrar pago simulado.
- Asociar pago a una reserva.
- Guardar método de pago.
- Guardar referencia de pago.
- Cambiar estado del pago.

---

### Notificaciones por correo electrónico

El sistema contempla notificaciones relacionadas con eventos importantes.

Funciones relacionadas:

- Registrar notificación por creación de cliente.
- Registrar notificación por confirmación de reserva.
- Guardar destinatario, asunto, mensaje, tipo de notificación y estado de envío.

---

## Estructura del proyecto

```text
ProyectoTravelers/
├── backend/                 API en FastAPI
│   ├── app/
│   │   ├── main.py          Punto de entrada, CORS y registro de routers
│   │   ├── core/            Constantes (roles, estados) y seguridad (JWT, bcrypt)
│   │   ├── database/        Conexión SQLAlchemy y Base declarativa
│   │   ├── models/          Modelos ORM (una tabla por archivo)
│   │   ├── schemas/         Esquemas Pydantic de entrada y salida
│   │   ├── repositories/    Acceso a datos
│   │   ├── services/        Reglas de negocio
│   │   └── routes/          Endpoints HTTP
│   ├── test/                Tests con pytest (usan DB_TEST_NAME)
│   ├── requirements.txt
│   └── .env.example
├── frontend/travelers/      Aplicación React + Vite
│   └── src/
│       ├── api/             Cliente axios con el token JWT
│       ├── components/      Navbar, rutas protegidas
│       ├── context/         AuthContext (sesión del usuario)
│       ├── utils/           Formato de moneda y fechas
│       └── pages/           Páginas de la aplicación
├── database/
│   └── script_BD_Travelers.sql
└── Varios/                  Documentación, imágenes y presentación
```

---

## Cómo ejecutar el proyecto

### 1. Base de datos

Ejecuta `database/script_BD_Travelers.sql` en MySQL. Crea `travelers_db` con roles, funcionalidades y ciudades.
Para los tests crea además una base vacía (por ejemplo `travelers_test_db`).

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

La documentación interactiva queda en `http://127.0.0.1:8000/docs`.

Para correr los tests:

```bash
cd backend
venv\Scripts\python -m pytest -q
```

### 3. Frontend

```bash
cd frontend/travelers
npm install
npm run dev
```

La aplicación queda en `http://localhost:5173`.

### Inicio de sesión con Google (opcional)

Los usuarios pueden registrarse o entrar con su cuenta de Google. Si el correo no existe se crea un cliente ya verificado; si existe, entra a esa misma cuenta.

1. En [Google Cloud Console](https://console.cloud.google.com/apis/credentials) crea un proyecto y configura la **pantalla de consentimiento de OAuth** (tipo *Externo*, agrega tu correo como usuario de prueba).
2. Ve a **Credenciales → Crear credenciales → ID de cliente de OAuth** y elige **Aplicación web**.
3. En **Orígenes autorizados de JavaScript** agrega `http://localhost:5173` y `http://localhost` (no hace falta ninguna URI de redireccionamiento).
4. Copia el ID de cliente en `backend/.env`:

```env
GOOGLE_CLIENT_ID=xxxxxxxxxxxx-xxxxxxxxxxxxxxxx.apps.googleusercontent.com
```

5. Reinicia el backend. El botón «Continuar con Google» aparece solo en login y registro (el frontend lo pide a `GET /users/google/config`).

El backend verifica el token con las llaves públicas de Google (`google-auth`): firma, expiración, emisor y que haya sido emitido para tu ID de cliente.

### Actualizar una base de datos existente

Si creaste la base antes de estos cambios, ejecuta en orden los scripts de migración de `database/` (solo agregan columnas):

1. `migracion_001_google_usuarios.sql`
2. `migracion_002_avatar_y_cancelaciones.sql`
3. `migracion_003_pagos_proveedores.sql`
4. `migracion_004_estado_envio_correos.sql`
5. `migracion_005_mejoras.sql` (reseñas, favoritos, cupones, notificaciones, bitácora, recordatorios y coordenadas de las ciudades)
6. `migracion_006_incluye_paquetes.sql` (qué incluye cada paquete)

### Fotos de perfil

Se suben desde **Mi cuenta → Información personal** (o el botón de cámara sobre la foto). El navegador las recorta en cuadrado y las reduce a 512 px; el backend acepta JPG, PNG o WEBP de hasta 2 MB y revisa el contenido real del archivo.

Se guardan en **S3**, en el mismo bucket de las imágenes de los paquetes, dentro de `avatars/`, y se muestran por **CloudFront**. En la base (`usuarios.foto_url`) solo queda la clave (`avatars/21_ab12….jpg`); la URL se arma con `CLOUDFRONT_URL`. El backend no guarda archivos en su disco. Las cuentas de Google usan su foto de Google hasta que suban una propia.

Configuración en `backend/.env`:

```env
S3_BUCKET=nombre-de-tu-bucket
AWS_REGION=us-east-1
# Solo en desarrollo local (en EC2 usa un rol IAM en la instancia):
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

Permiso IAM mínimo (usuario de desarrollo o rol de la instancia EC2):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:DeleteObject"],
    "Resource": "arn:aws:s3:::nombre-de-tu-bucket/avatars/*"
  }]
}
```

### Política de cancelación

| Cuándo cancela el cliente | Resultado |
|---|---|
| Hasta 7 días antes del viaje | Sin penalidad: se reembolsa todo lo pagado |
| Menos de 7 días antes | Penalidad del 30 % de lo pagado; se reembolsa el 70 % |
| Desde el día del viaje | No se puede cancelar |
| Reserva sin pagar | Se cancela sin costo en cualquier momento antes del viaje |

Los días y el porcentaje se cambian en *Consola → Configuración* (valores iniciales en `CANCELLATION_FREE_DAYS` y `CANCELLATION_PENALTY_PERCENT`). Si el administrador cancela la reserva desde la consola no hay penalidad: se reembolsa todo. Los reembolsos son simulados: el pago queda como `reembolsado` o `reembolso_parcial` y la reserva guarda la penalidad y el reembolso.

### Crear un administrador

Los usuarios se registran como clientes (`rol_id = 2`). Para tener un administrador cambia el rol en la base de datos:

```sql
UPDATE usuarios SET rol_id = 1 WHERE email = 'tu_correo@ejemplo.com';
```

---

## Flujo principal en el frontend

1. El usuario se registra y verifica su correo.
2. Inicia sesión y completa su **perfil de cliente** (identificación, fecha de nacimiento y ciudad).
3. Elige un paquete en **Paquetes turísticos**, ve el detalle y la galería, y reserva indicando fecha, personas y acompañantes.
4. En **Mis reservas** paga la reserva (pago simulado) o la cancela mientras esté pendiente.
5. El administrador entra al **Panel administrador** para ver reservas, pagos, paquetes, usuarios y proveedores, y aprobar o rechazar proveedores.

---

## Endpoints principales

| Módulo | Endpoints |
|---|---|
| Usuarios | `POST /users/`, `POST /users/login`, `POST /users/google`, `GET /users/google/config`, `POST /users/me/avatar`, `DELETE /users/me/avatar`, `GET /users/me`, `GET /users/verify-email`, `POST /users/forgot-password`, `POST /users/reset-password`, `GET /users/{id}/overview` (admin, ficha completa: cuenta, perfiles, reservas, pagos, productos, órdenes y correos) |
| Clientes | `POST /clients/me`, `GET /clients/me`, `GET /clients/` (admin) |
| Proveedores | `POST /providers/me`, `GET /providers/pending` (admin), `PATCH /providers/{id}/verification-status` (admin) |
| Productos | `POST /products/`, `GET /products/`, `GET /products/admin` |
| Paquetes | `GET /packages/`, `GET /packages/{id}`, `GET /packages/admin/{id}` (admin, con productos), `POST /packages/` (admin), `PATCH /packages/{id}` (admin, datos y productos), `PATCH /packages/{id}/status` (admin) |
| Imágenes | `GET /packages/{id}/images`, `GET /packages/{id}/images/cover`, `GET /packages/images/covers`, `POST /packages/{id}/images` (admin), `POST /packages/{id}/images/upload` (admin, sube a S3), `PATCH /packages/{id}/images/{id_imagen}/cover` (admin), `DELETE /packages/{id}/images/{id_imagen}` (admin) |
| Reservas | `POST /reservations/`, `GET /reservations/me`, `GET /reservations/availability/{id_paquete}`, `GET /reservations/cancellation-policy`, `GET /reservations/{id}/cancellation`, `PATCH /reservations/{id}/cancel`, `GET /reservations/` (admin), `PATCH /reservations/{id}/status` (admin) |
| Pagos | `POST /payments/`, `GET /payments/me`, `GET /payments/` (admin) |
| Ciudades | `GET /cities/` (con latitud y longitud), `POST /cities/`, `PATCH /cities/{id}` (admin) |
| Pagos a proveedores | `GET /provider-payments/` (admin), `GET /provider-payments/me` (proveedor), `GET /provider-payments/{id}`, `PATCH /provider-payments/{id}/approve`, `/pay`, `/annul` (admin), `POST /provider-payments/generate` (admin) |
| Configuración | `GET /settings/`, `PATCH /settings/` (admin) |
| Catálogos | `GET /products/types`, `GET /products/units` |
| Notificaciones (campana) | `GET /notifications/app`, `PATCH /notifications/app/{id}/read`, `PATCH /notifications/app/read-all` |
| Favoritos | `GET /favorites/`, `GET /favorites/ids`, `POST /favorites/{id_paquete}`, `DELETE /favorites/{id_paquete}` |
| Reseñas | `GET /reviews/summary`, `GET /reviews/package/{id}` (públicos), `GET /reviews/me`, `GET /reviews/me/pending`, `POST /reviews/`, `GET /reviews/` y `PATCH /reviews/{id}/status` (admin) |
| Cupones | `POST /coupons/validate`, `GET/POST /coupons/`, `PATCH/DELETE /coupons/{id}` (admin) |
| Voucher | `GET /vouchers/{id_reserva}` (PDF con QR), `GET /vouchers/verify/{codigo}` (público, lo abre el QR) |
| Recordatorios | `POST /reminders/run` (admin; también corren solos cada hora) |
| Reportes | `GET /reports/summary?desde&hasta`, `GET /reports/export?formato=xlsx\|pdf&desde&hasta` (admin) |
| Bitácora | `GET /audit/?entidad&desde&hasta&buscar` (admin) |

---

## Mejoras para viajeros y administradores

- **Reseñas con estrellas:** el viajero califica (1 a 5 estrellas y comentario) cada viaje confirmado después de su fecha, una vez por reserva, desde *Mis reservas* o *Mi cuenta → Mis reseñas*. Se publican con nombre e inicial del apellido; el promedio aparece en las tarjetas y en el detalle del paquete. El administrador puede ocultarlas en *Consola → Reseñas*.
- **Favoritos:** el corazón de cada paquete lo guarda en *Mi cuenta → Favoritos*.
- **Cupones:** se crean en *Consola → Cupones* (porcentaje o valor fijo, vigencia, usos máximos y compra mínima). El viajero lo aplica al reservar y el descuento queda en la reserva (`descuento_cupon`). Un cupón usado no se elimina, se desactiva.
- **Voucher PDF con QR:** en *Mis reservas*, las reservas confirmadas tienen el botón *Voucher PDF*. El QR abre `/verificar/{codigo}`, que muestra si la reserva es válida. Usa `FRONTEND_URL` para armar el enlace.
- **Recordatorios:** el backend revisa cada hora las reservas confirmadas y envía correo + aviso en la campana los días configurados antes del viaje (*Consola → Configuración*, por defecto 3). Se desactiva con `REMINDERS_ENABLED=false`.
- **Notificaciones en la app:** campana en la barra con los avisos de reservas, pagos, cancelaciones, solicitudes y pagos a proveedores.
- **Reportes:** *Consola → Reportes* con indicadores, ventas por mes, paquetes más vendidos, estados y destinos; se exportan a Excel (con gráficas) y PDF.
- **Bitácora:** cada cambio exitoso de un administrador queda registrado (quién, qué y cuándo) en *Consola → Bitácora*. Lo registra un middleware (`app/core/audit_middleware.py`).
- **Qué incluye:** al crear o editar un paquete se marcan las inclusiones (alojamiento, desayunos, transporte, tiquetes, tours, seguro…) y se pueden escribir otras. Si no se marca nada, la página muestra la frase «Incluye …» de la descripción o, si tampoco hay, los productos del paquete.
- **Ciudades:** al agregar una ciudad, el servidor busca sola su ubicación en OpenStreetMap (Nominatim); se desactiva con `GEOCODING_ENABLED=false`.
- **Paginación** en las tablas de la consola (10, 25 o 50 por página).
- **Mapa de destinos** en la portada (Leaflet con mapa base de Esri). Las ciudades necesitan latitud y longitud, que se editan en *Consola → Ciudades*.

---

## Proveedores y pagos a proveedores

1. Una persona se registra eligiendo **Proveedor** (o lo solicita después en *Mi cuenta → Ser proveedor*). La solicitud queda **pendiente**.
2. El administrador la aprueba en *Consola → Proveedores*; la cuenta pasa a rol proveedor y aparece **Mi panel** (`/proveedor`).
3. El proveedor configura sus productos (tipo, unidad de cobro, costo, ciudad), y sus **datos bancarios** en *Mi empresa*.
4. Cuando un viajero **paga** una reserva, se crea una **orden de pago** por cada proveedor del paquete:
   `costo × cantidad incluida × viajeros` (los productos *por servicio* no se multiplican por viajeros).
   Vence N días después del viaje (*Consola → Configuración*, por defecto 15).
5. El administrador **aprueba** y luego **marca como pagada** cada orden con la referencia de la transferencia (simulada), en *Consola → Pagos a proveedores*.
6. Si la reserva se cancela, las órdenes que aún no se pagaron quedan **anuladas**.

Para cargar productos de ejemplo en los 10 paquetes: `venv\Scripts\python -m scripts.seed_productos` (desde `backend`).

---

## Despliegue en AWS EC2

Producción: **https://travelers-sena.duckdns.org** (Ubuntu 24.04, t3.micro, IP elástica 52.72.14.150).

| Pieza | Dónde |
|---|---|
| Backend (FastAPI + uvicorn) | `/opt/travelers/backend`, servicio `travelers` (systemd), escucha en `127.0.0.1:8000` |
| Variables de entorno | `/opt/travelers/backend/.env` (permisos 600; clave JWT y contraseña de MySQL propias del servidor) |
| Frontend (build de Vite) | `/opt/travelers/frontend`, servido por Nginx |
| Nginx | `/etc/nginx/sites-available/travelers`: la página en `/` y el API en `/api/` |
| Base de datos | MySQL 8 local, base `travelers_db`, usuario `travelers` (solo localhost) |
| HTTPS | Let's Encrypt con Certbot; se renueva solo (`certbot.timer`) |
| Dominio | DuckDNS (`travelers-sena`) apuntando a la IP elástica |

**Actualizar el backend** (desde `backend/`):

```bash
tar --exclude=venv --exclude=__pycache__ --exclude=.env --exclude=test -czf - app scripts requirements.txt | ssh -i travelers-backend-key.pem ubuntu@52.72.14.150 "cd /opt/travelers/backend && tar -xzf - && venv/bin/pip install -q -r requirements.txt && sudo systemctl restart travelers"
```

**Actualizar el frontend** (desde `frontend/travelers/`):

```bash
VITE_API_URL=https://travelers-sena.duckdns.org/api npx vite build --outDir dist-prod --emptyOutDir
tar -czf - -C dist-prod . | ssh -i travelers-backend-key.pem ubuntu@52.72.14.150 "rm -rf /opt/travelers/frontend && mkdir -p /opt/travelers/frontend && tar -xzf - -C /opt/travelers/frontend"
```

**Ver los registros del backend:** `sudo journalctl -u travelers -f`

Si se cambian tablas, aplica la migración también en el servidor (`sudo mysql travelers_db < migracion_00X.sql`). El grupo de seguridad permite SSH solo desde el rango 190.7.115.0/24; si cambia tu proveedor de internet, ajusta esa regla.
