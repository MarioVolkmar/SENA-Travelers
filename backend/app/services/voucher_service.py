import io
import os
from datetime import timedelta
from decimal import Decimal

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.core.constants import ADMIN_ROLE_ID, IVA_PERCENT, RESERVATION_STATUS_CONFIRMED
from app.core.taxes import split_iva
from app.models.city_model import CityModel
from app.models.client_model import ClientModel
from app.models.companion_model import CompanionModel
from app.models.payment_model import PaymentModel
from app.models.reservation_model import ReservationModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.user_model import UserModel
from app.services.review_service import short_name

NIGHT = colors.HexColor("#0b1520")
SURFACE = colors.HexColor("#121e2b")
ORANGE = colors.HexColor("#f5a524")
TEAL = colors.HexColor("#5fc4cc")
INK = colors.HexColor("#1d2733")
MUTED = colors.HexColor("#6b7785")
LINE = colors.HexColor("#d9dee4")

MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def long_date(value):
    return f"{value.day} de {MONTHS[value.month - 1]} de {value.year}"


def money(value):
    return f"$ {Decimal(value or 0):,.0f}".replace(",", ".")


def frontend_url():
    return os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")


class VoucherService:
    """Voucher en PDF de una reserva confirmada, con QR para verificarla."""

    def __init__(self, db: Session):
        self.db = db

    def _load(self, reservation: ReservationModel):
        package = (
            self.db.query(TouristPackageModel)
            .filter(TouristPackageModel.id_paquete_turistico == reservation.id_paquete_turistico)
            .first()
        )
        city = self.db.query(CityModel).filter(CityModel.id_ciudad == package.ciudad_id).first() if package else None
        client = self.db.query(ClientModel).filter(ClientModel.id_cliente == reservation.cliente_id).first()
        user = self.db.query(UserModel).filter(UserModel.id_usuario == client.usuario_id).first() if client else None
        return package, city, client, user

    # ---------------------------------------------------------------
    # Verificación pública (lo que abre el QR)
    # ---------------------------------------------------------------

    def verify(self, codigo: str):
        reservation = (
            self.db.query(ReservationModel)
            .filter(ReservationModel.codigo_reserva == (codigo or "").strip().upper())
            .first()
        )
        if reservation is None:
            raise LookupError("No encontramos una reserva con ese código")

        package, city, _, user = self._load(reservation)
        return {
            "codigo_reserva": reservation.codigo_reserva,
            "estado": reservation.estado,
            "valida": reservation.estado == RESERVATION_STATUS_CONFIRMED,
            "paquete": package.nombre if package else "",
            "destino": city.nombre if city else "",
            "fecha_reserva": reservation.fecha_reserva,
            "cantidad_personas": reservation.cantidad_personas,
            "titular": short_name(user.nombre) if user else "",
        }

    # ---------------------------------------------------------------
    # PDF
    # ---------------------------------------------------------------

    def build_pdf(self, id_reserva: int, current_user: UserModel) -> tuple[bytes, str]:
        reservation = self.db.query(ReservationModel).filter(ReservationModel.id_reserva == id_reserva).first()
        if reservation is None:
            raise LookupError("La reserva no existe")

        package, city, client, user = self._load(reservation)

        if current_user.rol_id != ADMIN_ROLE_ID and (user is None or user.id_usuario != current_user.id_usuario):
            raise PermissionError("Solo puedes descargar el voucher de tus reservas")
        if reservation.estado != RESERVATION_STATUS_CONFIRMED:
            raise ValueError("El voucher está disponible cuando la reserva está confirmada (pagada)")

        companions = self.db.query(CompanionModel).filter(CompanionModel.reserva_id == reservation.id_reserva).all()
        payment = self.db.query(PaymentModel).filter(PaymentModel.reserva_id == reservation.id_reserva).first()

        nights = (package.fecha_fin - package.fecha_inicio).days if package else 0
        return_date = reservation.fecha_reserva + timedelta(days=nights)

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setTitle(f"Voucher {reservation.codigo_reserva}")
        width, height = A4
        margin = 18 * mm

        # Encabezado oscuro
        pdf.setFillColor(NIGHT)
        pdf.rect(0, height - 62 * mm, width, 62 * mm, stroke=0, fill=1)
        pdf.setFillColor(ORANGE)
        pdf.rect(0, height - 63.5 * mm, width, 1.5 * mm, stroke=0, fill=1)

        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 24)
        pdf.drawString(margin, height - 22 * mm, "TRAVELERS")
        pdf.setFont("Helvetica", 9)
        pdf.setFillColor(TEAL)
        pdf.drawString(margin, height - 28 * mm, "VOUCHER DE VIAJE")

        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 17)
        title = package.nombre.upper() if package else "PAQUETE"
        pdf.drawString(margin, height - 42 * mm, title[:48])
        pdf.setFont("Helvetica", 11)
        pdf.setFillColor(colors.HexColor("#c9d2db"))
        pdf.drawString(margin, height - 49 * mm, f"{city.nombre}, {city.departamento}" if city else "")

        # QR a la página pública de verificación
        qr_size = 40 * mm
        qr = QrCodeWidget(f"{frontend_url()}/verificar/{reservation.codigo_reserva}")
        bounds = qr.getBounds()
        drawing = Drawing(qr_size, qr_size, transform=[
            qr_size / (bounds[2] - bounds[0]), 0, 0, qr_size / (bounds[3] - bounds[1]), 0, 0,
        ])
        drawing.add(qr)
        qr_x = width - margin - qr_size
        qr_y = height - 57 * mm
        pdf.setFillColor(colors.white)
        pdf.roundRect(qr_x - 2 * mm, qr_y - 2 * mm, qr_size + 4 * mm, qr_size + 4 * mm, 3 * mm, stroke=0, fill=1)
        renderPDF.draw(drawing, pdf, qr_x, qr_y)

        # Código grande y estado
        y = height - 80 * mm
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(margin, y + 9 * mm, "CÓDIGO DE RESERVA")
        pdf.setFillColor(INK)
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawString(margin, y, reservation.codigo_reserva)

        pdf.setFillColor(colors.HexColor("#dcfce7"))
        pdf.roundRect(width - margin - 38 * mm, y - 1 * mm, 38 * mm, 9 * mm, 4.5 * mm, stroke=0, fill=1)
        pdf.setFillColor(colors.HexColor("#166534"))
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawCentredString(width - margin - 19 * mm, y + 2 * mm, "CONFIRMADA")

        # Datos del viaje en tres columnas
        y -= 20 * mm
        columns = [
            ("SALIDA", long_date(reservation.fecha_reserva)),
            ("REGRESO", long_date(return_date)),
            ("VIAJEROS", f"{reservation.cantidad_personas} {'persona' if reservation.cantidad_personas == 1 else 'personas'}"),
        ]
        col_width = (width - 2 * margin) / 3
        for index, (label, value) in enumerate(columns):
            x = margin + index * col_width
            pdf.setFillColor(MUTED)
            pdf.setFont("Helvetica-Bold", 8)
            pdf.drawString(x, y + 6 * mm, label)
            pdf.setFillColor(INK)
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(x, y, value)

        y -= 10 * mm
        pdf.setStrokeColor(LINE)
        pdf.line(margin, y, width - margin, y)

        # Viajeros
        y -= 10 * mm
        pdf.setFillColor(INK)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(margin, y, "Viajeros")
        y -= 8 * mm

        travelers = [(user.nombre if user else "Titular", client.identificacion if client else "", "Titular")]
        travelers += [(c.nombre, c.documento, "Acompañante") for c in companions]
        for name, document, role in travelers:
            pdf.setFont("Helvetica-Bold", 10)
            pdf.setFillColor(INK)
            pdf.drawString(margin, y, name[:50])
            pdf.setFont("Helvetica", 10)
            pdf.setFillColor(MUTED)
            pdf.drawString(margin + 90 * mm, y, f"Doc. {document}")
            pdf.drawRightString(width - margin, y, role)
            y -= 7 * mm

        y -= 3 * mm
        pdf.line(margin, y, width - margin, y)

        # Resumen de pago
        y -= 10 * mm
        pdf.setFillColor(INK)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(margin, y, "Pago")
        rows = []
        if reservation.descuento_cupon:
            rows.append(("Descuento con cupón", f"- {money(reservation.descuento_cupon)}"))
        # Desglose del IVA: el total pagado ya lo incluye
        base, iva = split_iva(reservation.total_reserva)
        rows.append(("Valor sin IVA", money(base)))
        rows.append((f"IVA ({IVA_PERCENT} %)", money(iva)))
        if payment is not None:
            rows.append(("Método", payment.metodo_pago.replace("_", " ").capitalize()))
            rows.append(("Referencia", payment.referencia_pago))
        for label, value in rows:
            y -= 7 * mm
            pdf.setFont("Helvetica", 10)
            pdf.setFillColor(MUTED)
            pdf.drawString(margin, y, label)
            pdf.setFillColor(INK)
            pdf.drawRightString(width - margin, y, value)

        y -= 11 * mm
        pdf.setFillColor(colors.HexColor("#fff4de"))
        pdf.roundRect(margin, y - 4 * mm, width - 2 * margin, 13 * mm, 3 * mm, stroke=0, fill=1)
        pdf.setFillColor(INK)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(margin + 5 * mm, y, "Total pagado (IVA incluido)")
        pdf.setFillColor(colors.HexColor("#b26b00"))
        pdf.drawRightString(width - margin - 5 * mm, y, money(reservation.total_reserva))

        # Indicaciones
        y -= 20 * mm
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 9)
        for line in [
            "Presenta este voucher (impreso o en el celular) y el documento de identidad de cada viajero.",
            "El código QR permite verificar la reserva en línea.",
            f"Verificación: {frontend_url()}/verificar/{reservation.codigo_reserva}",
        ]:
            pdf.drawString(margin, y, line)
            y -= 5.5 * mm

        # Pie
        pdf.setFillColor(NIGHT)
        pdf.rect(0, 0, width, 14 * mm, stroke=0, fill=1)
        pdf.setFillColor(colors.HexColor("#c9d2db"))
        pdf.setFont("Helvetica", 8)
        pdf.drawString(margin, 5.5 * mm, "Travelers · Vive viajando")
        pdf.drawRightString(width - margin, 5.5 * mm, f"Reserva comprada el {long_date(reservation.fecha_compra)}"
                            if reservation.fecha_compra else "")

        pdf.showPage()
        pdf.save()
        return buffer.getvalue(), f"voucher-{reservation.codigo_reserva}.pdf"
