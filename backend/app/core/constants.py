# Roles
ADMIN_ROLE_ID = 1
CLIENT_ROLE_ID = 2
PROVIDER_ROLE_ID = 3


# User status
USER_STATUS_ACTIVE = "activo"
USER_STATUS_INACTIVE = "inactivo"

ALLOWED_USER_STATUS = [
    USER_STATUS_ACTIVE,
    USER_STATUS_INACTIVE
]


# Email verification status
EMAIL_VERIFICATION_PENDING = "pendiente"
EMAIL_VERIFICATION_VERIFIED = "verificado"

ALLOWED_EMAIL_VERIFICATION_STATUS = [
    EMAIL_VERIFICATION_PENDING,
    EMAIL_VERIFICATION_VERIFIED
]


# Provider verification status
PROVIDER_STATUS_PENDING = "pendiente"
PROVIDER_STATUS_APPROVED = "aprobado"
PROVIDER_STATUS_REJECTED = "rechazado"

ALLOWED_PROVIDER_VERIFICATION_STATUS = [
    PROVIDER_STATUS_PENDING,
    PROVIDER_STATUS_APPROVED,
    PROVIDER_STATUS_REJECTED
]



# Product status
PRODUCT_STATUS_ACTIVE = "activo"
PRODUCT_STATUS_INACTIVE = "inactivo"

ALLOWED_PRODUCT_STATUS = [
    PRODUCT_STATUS_ACTIVE,
    PRODUCT_STATUS_INACTIVE
]

# Catálogo de tipos de producto: clave → (nombre, ejemplos)
PRODUCT_TYPES = {
    "hospedaje": ("Hospedaje", "Hotel, hostal, cabaña, glamping"),
    "alimentacion": ("Alimentación", "Desayuno, almuerzo, cena, menú típico"),
    "transporte": ("Transporte", "Bus, van, lancha, traslado al aeropuerto"),
    "tour": ("Tour guiado", "City tour, recorrido histórico o cultural"),
    "actividad": ("Actividad", "Rafting, buceo, caminata, parapente"),
    "entrada": ("Entrada", "Parques, museos, reservas naturales"),
    "seguro": ("Seguro de viaje", "Asistencia médica durante el viaje"),
    "otro": ("Otro", "Servicios que no encajan en los anteriores"),
}

# Notification email status
EMAIL_STATUS_PENDING = "pendiente"
EMAIL_STATUS_SENT = "enviado"
EMAIL_STATUS_FAILED = "fallido"
EMAIL_STATUS_DISABLED = "desactivado"  # EMAILS_ENABLED=false: se registra pero no se envía

ALLOWED_NOTIFICATION_EMAIL_STATUS = [
    EMAIL_STATUS_PENDING,
    EMAIL_STATUS_SENT,
    EMAIL_STATUS_FAILED,
    EMAIL_STATUS_DISABLED
]

# Notification types
NOTIFICATION_TYPE_EMAIL_VERIFICATION = "verificacion_email"
NOTIFICATION_TYPE_RESERVATION_CONFIRMATION = "confirmacion_reserva"
NOTIFICATION_TYPE_PAYMENT_CONFIRMATION = "confirmacion_pago"
NOTIFICATION_TYPE_PASSWORD_RESET = "recuperacion_password"
NOTIFICATION_TYPE_RESERVATION_CANCELLATION = "cancelacion_reserva"
NOTIFICATION_TYPE_TRIP_REMINDER = "recordatorio_viaje"

# Tourist package status
TOURIST_PACKAGE_STATUS_ACTIVE = "activo"
TOURIST_PACKAGE_STATUS_INACTIVE = "inactivo"

ALLOWED_TOURIST_PACKAGE_STATUS = [
    TOURIST_PACKAGE_STATUS_ACTIVE,
    TOURIST_PACKAGE_STATUS_INACTIVE
]

# Reservation status
RESERVATION_STATUS_PENDING = "pendiente"
RESERVATION_STATUS_CONFIRMED = "confirmada"
RESERVATION_STATUS_CANCELLED = "cancelada"

ALLOWED_RESERVATION_STATUS = [
    RESERVATION_STATUS_PENDING,
    RESERVATION_STATUS_CONFIRMED,
    RESERVATION_STATUS_CANCELLED
]

# Payment status
PAYMENT_STATUS_APPROVED = "aprobado"
PAYMENT_STATUS_REJECTED = "rechazado"
PAYMENT_STATUS_CANCELLED = "cancelado"
PAYMENT_STATUS_REFUNDED = "reembolsado"
PAYMENT_STATUS_PARTIALLY_REFUNDED = "reembolso_parcial"

ALLOWED_PAYMENT_STATUS = [
    PAYMENT_STATUS_APPROVED,
    PAYMENT_STATUS_REJECTED,
    PAYMENT_STATUS_CANCELLED,
    PAYMENT_STATUS_REFUNDED,
    PAYMENT_STATUS_PARTIALLY_REFUNDED
]

# Política de cancelación de reservas
# - Gratis hasta CANCELLATION_FREE_DAYS días antes de la fecha de viaje.
# - Después se cobra CANCELLATION_PENALTY_PERCENT % de lo pagado y se reembolsa el resto.
# - Desde el día del viaje ya no se puede cancelar.
CANCELLATION_FREE_DAYS = 7
CANCELLATION_PENALTY_PERCENT = 30


# Unidad en que el proveedor cobra cada producto
PRODUCT_UNIT_PERSON = "persona"
PRODUCT_UNIT_NIGHT = "noche"
PRODUCT_UNIT_DAY = "dia"
PRODUCT_UNIT_SERVICE = "servicio"  # precio fijo por reserva, sin importar cuántos viajeros

PRODUCT_UNITS = {
    PRODUCT_UNIT_PERSON: "Por persona",
    PRODUCT_UNIT_NIGHT: "Por persona por noche",
    PRODUCT_UNIT_DAY: "Por persona por día",
    PRODUCT_UNIT_SERVICE: "Por servicio (grupo)",
}

# Órdenes de pago a proveedores
PROVIDER_ORDER_PENDING = "pendiente"
PROVIDER_ORDER_APPROVED = "aprobada"
PROVIDER_ORDER_PAID = "pagada"
PROVIDER_ORDER_CANCELLED = "anulada"

# Configuración editable por el administrador (tabla configuraciones)
SETTING_PROVIDER_PAYMENT_DAYS = "dias_pago_proveedores"
SETTING_CANCELLATION_FREE_DAYS = "dias_cancelacion_gratis"
SETTING_CANCELLATION_PENALTY_PERCENT = "porcentaje_penalidad_cancelacion"
SETTING_REMINDER_DAYS = "dias_recordatorio_viaje"
DEFAULT_SETTINGS = {
    SETTING_REMINDER_DAYS: "3",
    SETTING_PROVIDER_PAYMENT_DAYS: "15",
    SETTING_CANCELLATION_FREE_DAYS: str(CANCELLATION_FREE_DAYS),
    SETTING_CANCELLATION_PENALTY_PERCENT: str(CANCELLATION_PENALTY_PERCENT),
}


# Cupones de descuento
COUPON_TYPE_PERCENT = "porcentaje"
COUPON_TYPE_AMOUNT = "valor"
COUPON_TYPES = (COUPON_TYPE_PERCENT, COUPON_TYPE_AMOUNT)
COUPON_STATUS_ACTIVE = "activo"
COUPON_STATUS_INACTIVE = "inactivo"

# Reseñas
REVIEW_STATUS_VISIBLE = "visible"
REVIEW_STATUS_HIDDEN = "oculta"

# Qué incluye un paquete (campo «incluye» de paquetes_turisticos)
PACKAGE_INCLUDE_TYPES = (
    "alojamiento",
    "desayuno",
    "alimentacion",
    "transporte",
    "vuelos",
    "traslados",
    "tours",
    "actividades",
    "entradas",
    "guia",
    "seguro",
    "asistencia",
)
