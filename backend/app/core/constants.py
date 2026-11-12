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
# IVA de Colombia. Los precios que ve el cliente YA lo incluyen (Estatuto del Consumidor,
# Ley 1480 de 2011, art. 26: el precio informado debe ser el total, con impuestos).
# El sistema solo lo desglosa: base sin IVA + IVA = total.
IVA_PERCENT = 19

# Límites razonables para precios y cantidades (en pesos colombianos).
# Son la única fuente: el frontend los lee de GET /config/limits (ver LIMITS más abajo).
PACKAGE_PRICE_MIN = 10_000            # precio por persona de un paquete
PACKAGE_PRICE_MAX = 20_000_000
PRODUCT_COST_MIN = 1_000              # costo de un producto (por persona, noche, día o servicio)
PRODUCT_COST_MAX = 10_000_000
PACKAGE_SLOTS_MIN = 1                 # cupo máximo de personas de un paquete
PACKAGE_SLOTS_MAX = 100
PACKAGE_DISCOUNT_MAX = 90             # descuento en %
PACKAGE_PRODUCT_QUANTITY_MAX = 30     # cantidad de un producto dentro del paquete (ej. noches)
RESERVATION_TRAVELERS_MAX = 10        # viajeros por reserva (titular + acompañantes)
COUPON_PERCENT_MAX = 90               # cupón por porcentaje
COUPON_VALUE_MIN = 1_000              # cupón por valor fijo, en pesos
COUPON_VALUE_MAX = 5_000_000
COUPON_USES_MAX = 10_000              # usos máximos de un cupón
COUPON_MIN_PURCHASE_MAX = 50_000_000  # compra mínima para usar un cupón

# Edades mínimas: el titular de la cuenta de viajero y cada acompañante (en la fecha del viaje)
MIN_CLIENT_AGE = 18
MIN_COMPANION_AGE = 7

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
SETTING_PAYMENT_HOURS = "horas_para_pagar"  # horas para pagar una reserva pendiente antes de que venza
SETTING_PROVIDER_PAYMENT_DAY = "dia_pago_proveedores"  # día del mes en que se pagan las órdenes aprobadas
DEFAULT_SETTINGS = {
    SETTING_PROVIDER_PAYMENT_DAY: "15",
    SETTING_REMINDER_DAYS: "3",
    SETTING_PAYMENT_HOURS: "24",
    SETTING_PROVIDER_PAYMENT_DAYS: "15",
    SETTING_CANCELLATION_FREE_DAYS: str(CANCELLATION_FREE_DAYS),
    SETTING_CANCELLATION_PENALTY_PERCENT: str(CANCELLATION_PENALTY_PERCENT),
}

# Rangos permitidos para cada valor de la configuración: (mínimo, máximo)
SETTING_RANGES = {
    SETTING_PROVIDER_PAYMENT_DAYS: (0, 180),
    SETTING_REMINDER_DAYS: (1, 30),
    SETTING_CANCELLATION_FREE_DAYS: (0, 90),
    SETTING_CANCELLATION_PENALTY_PERCENT: (0, 100),
    SETTING_PAYMENT_HOURS: (1, 168),
    SETTING_PROVIDER_PAYMENT_DAY: (1, 28),
}

# Días antes del plazo de aprobación en que se avisa a los administradores de una orden pendiente
ORDER_APPROVAL_REMINDER_DAYS = 2
# Comprobantes de pago a proveedores (imagen de la transferencia)
RECEIPT_PREFIX = "comprobantes/"


def _range(minimum, maximum):
    return {"min": minimum, "max": maximum}


# Todos los límites en un solo lugar. El frontend los pide a GET /config/limits,
# así los formularios nunca quedan con valores distintos a los que valida el backend.
LIMITS = {
    "packagePrice": _range(PACKAGE_PRICE_MIN, PACKAGE_PRICE_MAX),
    "productCost": _range(PRODUCT_COST_MIN, PRODUCT_COST_MAX),
    "packageSlots": _range(PACKAGE_SLOTS_MIN, PACKAGE_SLOTS_MAX),
    "packageDiscount": _range(0, PACKAGE_DISCOUNT_MAX),
    "packageProductQuantity": _range(1, PACKAGE_PRODUCT_QUANTITY_MAX),
    "reservationTravelers": _range(1, RESERVATION_TRAVELERS_MAX),
    "couponPercent": _range(1, COUPON_PERCENT_MAX),
    "couponValue": _range(COUPON_VALUE_MIN, COUPON_VALUE_MAX),
    "couponUses": _range(1, COUPON_USES_MAX),
    "couponMinPurchase": _range(0, COUPON_MIN_PURCHASE_MAX),
    "providerPaymentDays": _range(*SETTING_RANGES[SETTING_PROVIDER_PAYMENT_DAYS]),
    "reminderDays": _range(*SETTING_RANGES[SETTING_REMINDER_DAYS]),
    "freeCancellationDays": _range(*SETTING_RANGES[SETTING_CANCELLATION_FREE_DAYS]),
    "cancellationPenalty": _range(*SETTING_RANGES[SETTING_CANCELLATION_PENALTY_PERCENT]),
    "paymentHours": _range(*SETTING_RANGES[SETTING_PAYMENT_HOURS]),
    "providerPaymentDay": _range(*SETTING_RANGES[SETTING_PROVIDER_PAYMENT_DAY]),
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
