"""
Pagos con Stripe Checkout (modo de prueba).

Flujo:
1. checkout(): valida la reserva y crea una "Checkout Session" en Stripe con el valor
   de la reserva. Stripe devuelve la URL de su página de pago.
2. El viajero paga allá (tarjeta de prueba 4242 4242 4242 4242) y Stripe lo devuelve a
   /reservations?stripe_session=<id de la sesión>.
3. confirm(): al volver, el backend consulta la sesión en Stripe y confirma la reserva.
4. handle_webhook(): Stripe también avisa al webhook (checkout.session.completed),
   firmado con el secreto whsec_...; así se confirma aunque el viajero cierre la ventana.

Las dos vías terminan en process_session(), que no registra un pago dos veces.
Con una llave sk_test_/rk_test_ todo ocurre en modo de prueba: no se mueve dinero.
Documentación: https://docs.stripe.com/payments/checkout
"""
import hashlib
import hmac
import logging
import os
import time
from decimal import Decimal
from types import SimpleNamespace

import requests
from sqlalchemy.orm import Session

from app.core.constants import ADMIN_ROLE_ID, IVA_PERCENT, RESERVATION_STATUS_PENDING
from app.core.taxes import split_iva
from app.models.client_model import ClientModel
from app.models.reservation_model import ReservationModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.user_model import UserModel
from app.repositories.client_repository import ClientRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.reservation_repository import ReservationRepository
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

API_URL = "https://api.stripe.com/v1"
CURRENCY = "cop"
WEBHOOK_TOLERANCE_SECONDS = 300   # firmas de más de 5 minutos se rechazan (evita reenvíos viejos)

METHOD_LABELS = {"card": "Tarjeta", "link": "Link"}

STATUS_MESSAGES = {
    "paid": "Pago aprobado. Tu reserva quedó confirmada.",
    "unpaid": "El pago no se completó. Puedes intentarlo de nuevo.",
    "no_payment_required": "La reserva no requería pago.",
}


class StripeNotConfigured(Exception):
    """Falta STRIPE_SECRET_KEY en el .env: se sigue usando el pago simulado."""


def secret_key() -> str:
    return os.getenv("STRIPE_SECRET_KEY", "").strip()


def webhook_secret() -> str:
    return os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()


def is_enabled() -> bool:
    return bool(secret_key())


def is_test_mode() -> bool:
    return "_test_" in secret_key()


def pesos(value) -> str:
    return f"${value:,.0f}".replace(",", ".")


def frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")


def amount_in_cents(value) -> int:
    """Stripe maneja el peso colombiano con dos decimales: $1.250.000 → 125000000."""
    return int((Decimal(value) * 100).quantize(Decimal("1")))


def verify_signature(payload: bytes, header: str, secret: str, now: float | None = None) -> None:
    """
    Verifica el encabezado Stripe-Signature ("t=<hora>,v1=<firma>,...").
    La firma es HMAC-SHA256 de "<t>.<cuerpo>" con el secreto del webhook.
    """
    parts = {}
    for item in (header or "").split(","):
        key, _, value = item.strip().partition("=")
        parts.setdefault(key, []).append(value)

    timestamp = (parts.get("t") or [""])[0]
    signatures = parts.get("v1") or []
    if not timestamp.isdigit() or not signatures:
        raise PermissionError("Firma del webhook inválida")

    signed = f"{timestamp}.".encode() + payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, signature) for signature in signatures):
        raise PermissionError("Firma del webhook inválida")

    if abs((now or time.time()) - int(timestamp)) > WEBHOOK_TOLERANCE_SECONDS:
        raise PermissionError("La firma del webhook está vencida")


class StripeService:
    def __init__(self, db: Session):
        self.db = db
        self.reservations = ReservationRepository(db)
        self.payments = PaymentRepository(db)
        self.clients = ClientRepository(db)

    # ------------------------------------------------------------ utilidades

    def _ensure_enabled(self):
        if not is_enabled():
            raise StripeNotConfigured("Los pagos con Stripe no están configurados")

    def _request(self, method: str, path: str, data: dict | None = None) -> dict:
        response = requests.request(
            method, f"{API_URL}{path}", data=data, auth=(secret_key(), ""), timeout=20
        )
        if response.status_code == 404:
            raise LookupError("La sesión de pago no existe en Stripe")
        if response.status_code >= 400:
            message = response.json().get("error", {}).get("message", "")
            logger.warning("Stripe respondió %s: %s", response.status_code, message)
            raise requests.HTTPError(message or f"Error {response.status_code} de Stripe")
        return response.json()

    def _owner_user(self, reservation: ReservationModel):
        client = self.db.query(ClientModel).filter(ClientModel.id_cliente == reservation.cliente_id).first()
        if client is None:
            return None
        return self.db.query(UserModel).filter(UserModel.id_usuario == client.usuario_id).first()

    def _own_pending_reservation(self, reserva_id: int, current_user: UserModel):
        client = self.clients.find_by_user_id(current_user.id_usuario)
        if client is None:
            raise PermissionError("Debes tener un perfil de cliente para realizar pagos")

        reservation = self.reservations.find_by_id(reserva_id)
        if reservation is None:
            raise LookupError("La reserva no existe")
        if reservation.cliente_id != client.id_cliente:
            raise PermissionError("Solo puedes pagar tus propias reservas")
        if reservation.estado != RESERVATION_STATUS_PENDING:
            raise ValueError("Solo se pueden pagar reservas pendientes")
        if self.payments.find_by_reservation_id(reservation.id_reserva) is not None:
            raise ValueError("La reserva ya tiene un pago registrado")
        self._reservations_service().ensure_payable_in_time(reservation)
        return reservation

    def _reservations_service(self):
        from app.services.reservation_service import ReservationService  # import local: evita ciclos

        return ReservationService(self.db)

    def _refund_late_payment(self, session: dict, reservation: ReservationModel):
        """Devuelve completo un pago que llegó cuando la reserva ya no se podía confirmar."""
        intent = session.get("payment_intent")
        intent_id = intent.get("id") if isinstance(intent, dict) else intent
        if not intent_id:
            return False
        try:
            self.refund(SimpleNamespace(referencia_pago=intent_id), reservation.total_reserva, reservation.codigo_reserva)
            return True
        except ValueError:
            return False

    def _package_name(self, reservation: ReservationModel) -> str:
        package = (
            self.db.query(TouristPackageModel)
            .filter(TouristPackageModel.id_paquete_turistico == reservation.id_paquete_turistico)
            .first()
        )
        return package.nombre if package else "Paquete turístico"

    def fetch_session(self, session_id: str) -> dict:
        # expand: trae el PaymentIntent para saber el método de pago usado. Una clave
        # restringida (rk_test_) puede no tener permiso para eso: entonces se pide la sesión sola.
        try:
            return self._request("GET", f"/checkout/sessions/{session_id}?expand[]=payment_intent.payment_method")
        except requests.HTTPError:
            return self._request("GET", f"/checkout/sessions/{session_id}")

    # ------------------------------------------------------------ flujo

    def checkout(self, reserva_id: int, current_user: UserModel) -> dict:
        """Crea la sesión de pago de Stripe y devuelve la URL a donde se envía al viajero."""
        self._ensure_enabled()
        reservation = self._own_pending_reservation(reserva_id, current_user)
        people = reservation.cantidad_personas

        session = self._request("POST", "/checkout/sessions", {
            "mode": "payment",
            "locale": "es",
            "customer_email": current_user.email,
            "client_reference_id": reservation.codigo_reserva,
            "metadata[codigo_reserva]": reservation.codigo_reserva,
            "metadata[reserva_id]": reservation.id_reserva,
            "line_items[0][quantity]": 1,
            "line_items[0][price_data][currency]": CURRENCY,
            "line_items[0][price_data][unit_amount]": amount_in_cents(reservation.total_reserva),
            "line_items[0][price_data][product_data][name]": self._package_name(reservation),
            "line_items[0][price_data][product_data][description]": (
                f"Reserva {reservation.codigo_reserva} · {people} {'persona' if people == 1 else 'personas'}"
                f" · IVA ({IVA_PERCENT} %) incluido: {pesos(split_iva(reservation.total_reserva)[1])}"
            ),
            # Stripe reemplaza {CHECKOUT_SESSION_ID} por el id real al devolver al viajero
            "success_url": f"{frontend_url()}/reservations?stripe_session={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{frontend_url()}/reservations?pago=cancelado",
            "expires_at": int(time.time()) + 30 * 60,   # la sesión vence en 30 minutos
        })
        return {"checkout_url": session["url"], "session_id": session["id"], "test_mode": not session.get("livemode")}

    def process_session(self, session: dict) -> dict:
        """
        Aplica una sesión de Stripe a su reserva. Solo una sesión pagada, en pesos y por el
        valor exacto confirma la reserva. Si el pago ya estaba registrado no hace nada.
        """
        code = (session.get("metadata") or {}).get("codigo_reserva") or session.get("client_reference_id")
        reservation = self.reservations.find_by_code(code or "")
        if reservation is None:
            raise LookupError("La sesión de pago no corresponde a ninguna reserva")

        status = session.get("payment_status")
        result = {
            "status": status,
            "codigo_reserva": reservation.codigo_reserva,
            "message": STATUS_MESSAGES.get(status, "Estado del pago desconocido."),
        }
        if status != "paid":
            return result

        if self.payments.find_by_reservation_id(reservation.id_reserva) is not None:
            return result  # ya se había registrado (por la otra vía)

        if session.get("currency") != CURRENCY or int(session.get("amount_total") or 0) != amount_in_cents(reservation.total_reserva):
            logger.warning("Stripe: monto distinto en %s: %s", reservation.codigo_reserva, session.get("amount_total"))
            raise ValueError("El valor pagado en Stripe no coincide con el total de la reserva")

        if reservation.estado != RESERVATION_STATUS_PENDING:
            # Caso típico: el plazo de pago venció mientras el viajero estaba en Stripe.
            # Si aún hay cupo, la reserva se reactiva y el pago se registra; si no, se devuelve el dinero.
            if not self._reservations_service().reactivate_expired(reservation):
                logger.warning("Stripe: pago para %s en estado %s", reservation.codigo_reserva, reservation.estado)
                if self._refund_late_payment(session, reservation):
                    raise ValueError("La reserva ya no estaba disponible, así que devolvimos el pago completo a tu medio de pago")
                raise ValueError("La reserva ya no está pendiente; contacta a la agencia para revisar el pago")
            logger.info("Stripe: %s se reactivó al llegar su pago después del plazo", reservation.codigo_reserva)

        intent = session.get("payment_intent")
        method_type = None
        if isinstance(intent, dict):
            method = intent.get("payment_method")
            method_type = method.get("type") if isinstance(method, dict) else None
            reference = intent.get("id")
        else:
            reference = intent or session.get("id")

        PaymentService(self.db).register_approved_payment(
            reservation=reservation,
            user=self._owner_user(reservation),
            metodo_pago=f"Stripe · {METHOD_LABELS.get(method_type, 'Tarjeta')}",
            valor=Decimal(reservation.total_reserva),
            referencia_pago=str(reference)[:45],
        )
        return result

    def confirm(self, session_id: str, current_user: UserModel) -> dict:
        """Al volver de Stripe: consulta la sesión y la aplica a la reserva del viajero."""
        self._ensure_enabled()
        session = self.fetch_session(session_id)

        code = (session.get("metadata") or {}).get("codigo_reserva") or session.get("client_reference_id")
        reservation = self.reservations.find_by_code(code or "")
        if reservation is None:
            raise LookupError("La sesión de pago no corresponde a ninguna reserva")
        if current_user.rol_id != ADMIN_ROLE_ID:
            owner = self._owner_user(reservation)
            if owner is None or owner.id_usuario != current_user.id_usuario:
                raise PermissionError("Este pago no es de una reserva tuya")

        return self.process_session(session)

    @staticmethod
    def is_stripe_payment(payment) -> bool:
        """Pagos hechos con Stripe: su referencia es el PaymentIntent (pi_...)."""
        return bool(
            payment is not None
            and (payment.metodo_pago or "").startswith("Stripe")
            and (payment.referencia_pago or "").startswith("pi_")
        )

    def refund(self, payment, amount, codigo_reserva: str) -> dict:
        """
        Devuelve dinero de un pago hecho con Stripe (total o parcial, según la penalidad).
        En modo de prueba el reembolso aparece en el panel de Stripe, pero no mueve dinero real.
        Si Stripe lo rechaza se lanza ValueError y la cancelación no se guarda.
        """
        self._ensure_enabled()
        cents = amount_in_cents(amount)
        if cents <= 0:
            return {"refunded": False}

        try:
            refund = self._request("POST", "/refunds", {
                "payment_intent": payment.referencia_pago,
                "amount": cents,
                "reason": "requested_by_customer",
                "metadata[codigo_reserva]": codigo_reserva,
            })
        except (requests.RequestException, LookupError) as error:
            logger.warning("Stripe: no se pudo reembolsar %s: %s", codigo_reserva, error)
            raise ValueError("No fue posible procesar el reembolso en Stripe. Intenta de nuevo en unos minutos.")

        logger.info("Stripe: reembolso %s de %s para %s", refund.get("id"), cents, codigo_reserva)
        return {"refunded": True, "refund_id": refund.get("id"), "status": refund.get("status")}

    def handle_webhook(self, payload: bytes, signature_header: str, event: dict) -> dict:
        """Webhook de Stripe: verifica la firma y aplica las sesiones pagadas."""
        if not webhook_secret():
            raise StripeNotConfigured("Falta STRIPE_WEBHOOK_SECRET para verificar los avisos de Stripe")

        verify_signature(payload, signature_header, webhook_secret())

        if event.get("type") not in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
            return {"ignored": True}

        session = (event.get("data") or {}).get("object") or {}
        return self.process_session(session)
