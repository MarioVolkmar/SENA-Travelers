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
SENA-Travelers/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── database/
│   │   │   └── connection.py
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── client.py
│   │   │   ├── provider.py
│   │   │   ├── product.py
│   │   │   ├── package.py
│   │   │   ├── reservation.py
│   │   │   └── payment.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── user_repository.py
│   │   │   ├── client_repository.py
│   │   │   ├── provider_repository.py
│   │   │   ├── product_repository.py
│   │   │   ├── package_repository.py
│   │   │   ├── reservation_repository.py
│   │   │   └── payment_repository.py
│   │   │
│   │   ├── services/
│   │   │   ├── user_service.py
│   │   │   ├── client_service.py
│   │   │   ├── provider_service.py
│   │   │   ├── product_service.py
│   │   │   ├── package_service.py
│   │   │   ├── reservation_service.py
│   │   │   ├── payment_service.py
│   │   │   └── email_service.py
│   │   │
│   │   └── routes/
│   │       ├── user_routes.py
│   │       ├── client_routes.py
│   │       ├── provider_routes.py
│   │       ├── product_routes.py
│   │       ├── package_routes.py
│   │       ├── reservation_routes.py
│   │       └── payment_routes.py
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── routes/
│   │   └── App.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
├── database/
│   └── schema.sql
│
├── docs/
│   ├── manual_usuario.md
│   ├── manual_tecnico.md
│   └── modelo_bd.png
│
├── .gitignore
└── README.md

