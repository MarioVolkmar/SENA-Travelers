import io
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import clock
from app.core.constants import (
    ADMIN_ROLE_ID,
    PAYMENT_STATUS_APPROVED,
    PAYMENT_STATUS_PARTIALLY_REFUNDED,
    PROVIDER_ORDER_CANCELLED,
    RESERVATION_STATUS_CANCELLED,
    REVIEW_STATUS_VISIBLE,
)
from app.models.city_model import CityModel
from app.models.payment_model import PaymentModel
from app.models.provider_payment_order_model import ProviderPaymentOrderModel
from app.models.reservation_model import ReservationModel
from app.models.review_model import ReviewModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.user_model import UserModel

MONTHS_SHORT = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
STATUS_LABELS = {"pendiente": "Pendiente", "confirmada": "Confirmada", "cancelada": "Cancelada"}
ZERO = Decimal("0")


def month_label(key: str) -> str:
    year, month = key.split("-")
    return f"{MONTHS_SHORT[int(month) - 1]} {year}"


def money(value) -> str:
    return f"$ {Decimal(value or 0):,.0f}".replace(",", ".")


def month_keys(start: date, end: date):
    keys = []
    current = date(start.year, start.month, 1)
    while current <= end:
        keys.append(f"{current.year}-{current.month:02d}")
        current = date(current.year + (current.month // 12), current.month % 12 + 1, 1)
    return keys


class ReportService:
    """Reportes de ventas y operación para la consola, con exportación a Excel y PDF."""

    def __init__(self, db: Session):
        self.db = db

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    @staticmethod
    def resolve_range(desde: date | None, hasta: date | None):
        hasta = hasta or clock.today()
        desde = desde or date(hasta.year - 1, hasta.month, 1) + timedelta(days=0)
        if desde > hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la final")
        if (hasta - desde).days > 366 * 3:
            raise ValueError("El rango máximo es de 3 años")
        return desde, hasta

    # ---------------------------------------------------------------
    # Datos
    # ---------------------------------------------------------------

    def build(self, current_user: UserModel, desde: date | None = None, hasta: date | None = None):
        self._ensure_admin(current_user)
        desde, hasta = self.resolve_range(desde, hasta)
        start, end = datetime.combine(desde, time.min), datetime.combine(hasta, time.max)

        reservations = (
            self.db.query(ReservationModel)
            .filter(ReservationModel.fecha_compra >= start, ReservationModel.fecha_compra <= end)
            .all()
        )
        packages = {p.id_paquete_turistico: p for p in self.db.query(TouristPackageModel).all()}
        cities = {c.id_ciudad: c.nombre for c in self.db.query(CityModel).all()}
        payments = {
            p.reserva_id: p
            for p in self.db.query(PaymentModel)
            .filter(PaymentModel.reserva_id.in_([r.id_reserva for r in reservations] or [0]))
            .all()
        }

        def net_sale(reservation):
            payment = payments.get(reservation.id_reserva)
            if payment is None:
                return ZERO
            if payment.estado_pago == PAYMENT_STATUS_APPROVED:
                return Decimal(payment.valor)
            if payment.estado_pago == PAYMENT_STATUS_PARTIALLY_REFUNDED:
                return Decimal(reservation.penalidad_cancelacion or 0)
            return ZERO

        keys = month_keys(desde, hasta)
        by_month = {key: {"ventas": ZERO, "reservas": 0, "viajeros": 0} for key in keys}
        by_status = defaultdict(int)
        by_package = defaultdict(lambda: {"reservas": 0, "viajeros": 0, "ventas": ZERO})
        by_city = defaultdict(lambda: {"reservas": 0, "ventas": ZERO})

        total_sales = ZERO
        travelers = 0
        coupon_discounts = ZERO
        paid_count = 0

        for reservation in reservations:
            sale = net_sale(reservation)
            key = f"{reservation.fecha_compra.year}-{reservation.fecha_compra.month:02d}"
            package = packages.get(reservation.id_paquete_turistico)
            city_name = cities.get(package.ciudad_id, "—") if package else "—"

            by_status[reservation.estado] += 1
            if key in by_month:
                by_month[key]["reservas"] += 1
                by_month[key]["ventas"] += sale

            total_sales += sale
            coupon_discounts += Decimal(reservation.descuento_cupon or 0)
            if sale > 0:
                paid_count += 1

            if reservation.estado != RESERVATION_STATUS_CANCELLED:
                travelers += reservation.cantidad_personas
                if key in by_month:
                    by_month[key]["viajeros"] += reservation.cantidad_personas

            name = package.nombre if package else f"Paquete #{reservation.id_paquete_turistico}"
            by_package[name]["reservas"] += 1
            by_package[name]["ventas"] += sale
            if reservation.estado != RESERVATION_STATUS_CANCELLED:
                by_package[name]["viajeros"] += reservation.cantidad_personas
            by_city[city_name]["reservas"] += 1
            by_city[city_name]["ventas"] += sale

        provider_costs = (
            self.db.query(func.coalesce(func.sum(ProviderPaymentOrderModel.monto), 0))
            .filter(
                ProviderPaymentOrderModel.reserva_id.in_([r.id_reserva for r in reservations] or [0]),
                ProviderPaymentOrderModel.estado != PROVIDER_ORDER_CANCELLED,
            )
            .scalar()
        )
        provider_costs = Decimal(provider_costs or 0)

        rating = (
            self.db.query(func.avg(ReviewModel.calificacion), func.count(ReviewModel.id_resena))
            .filter(ReviewModel.estado == REVIEW_STATUS_VISIBLE, ReviewModel.fecha >= start, ReviewModel.fecha <= end)
            .first()
        )

        total = len(reservations)
        cancelled = by_status.get(RESERVATION_STATUS_CANCELLED, 0)

        return {
            "desde": desde,
            "hasta": hasta,
            "kpis": {
                "ventas_netas": total_sales,
                "costo_proveedores": provider_costs,
                "margen": total_sales - provider_costs,
                "reservas": total,
                "viajeros": travelers,
                "ticket_promedio": (total_sales / paid_count).quantize(Decimal("1")) if paid_count else ZERO,
                "tasa_cancelacion": round(cancelled * 100 / total, 1) if total else 0,
                "descuentos_cupones": coupon_discounts,
                "calificacion_promedio": round(float(rating[0]), 1) if rating and rating[0] else None,
                "total_resenas": rating[1] if rating else 0,
            },
            "ventas_por_mes": [
                {"mes": key, "etiqueta": month_label(key), **values} for key, values in by_month.items()
            ],
            "reservas_por_estado": [
                {"estado": estado, "etiqueta": STATUS_LABELS.get(estado, estado), "total": count}
                for estado, count in sorted(by_status.items(), key=lambda item: -item[1])
            ],
            "top_paquetes": [
                {"paquete": name, **values}
                for name, values in sorted(by_package.items(), key=lambda item: (-item[1]["ventas"], -item[1]["reservas"]))[:8]
            ],
            "por_destino": [
                {"destino": name, **values}
                for name, values in sorted(by_city.items(), key=lambda item: -item[1]["ventas"])
            ],
        }

    # ---------------------------------------------------------------
    # Excel
    # ---------------------------------------------------------------

    def to_excel(self, report) -> bytes:
        workbook = Workbook()
        header_fill = PatternFill("solid", fgColor="0B1520")
        header_font = Font(bold=True, color="FFFFFF")
        title_font = Font(bold=True, size=16)

        def table(sheet, start_row, headers, rows, money_cols=()):
            for col, header in enumerate(headers, start=1):
                cell = sheet.cell(row=start_row, column=col, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")
            for r, row in enumerate(rows, start=start_row + 1):
                for c, value in enumerate(row, start=1):
                    cell = sheet.cell(row=r, column=c, value=float(value) if isinstance(value, Decimal) else value)
                    if c in money_cols:
                        cell.number_format = '"$" #,##0'
            for col in range(1, len(headers) + 1):
                sheet.column_dimensions[get_column_letter(col)].width = 24 if col == 1 else 16
            return start_row + len(rows)

        # Resumen
        summary = workbook.active
        summary.title = "Resumen"
        summary["A1"] = "Reporte Travelers"
        summary["A1"].font = title_font
        summary["A2"] = f"Del {report['desde']:%d/%m/%Y} al {report['hasta']:%d/%m/%Y}"
        k = report["kpis"]
        kpis = [
            ("Ventas netas", k["ventas_netas"]),
            ("Costo de proveedores", k["costo_proveedores"]),
            ("Margen", k["margen"]),
            ("Reservas", k["reservas"]),
            ("Viajeros", k["viajeros"]),
            ("Ticket promedio", k["ticket_promedio"]),
            ("Tasa de cancelación (%)", k["tasa_cancelacion"]),
            ("Descuentos con cupones", k["descuentos_cupones"]),
            ("Calificación promedio", k["calificacion_promedio"] or "Sin reseñas"),
        ]
        table(summary, 4, ["Indicador", "Valor"], kpis)
        for row in (5, 6, 7, 10, 12):
            summary.cell(row=row, column=2).number_format = '"$" #,##0'

        # Ventas por mes + gráfica
        months = workbook.create_sheet("Ventas por mes")
        last = table(
            months, 1, ["Mes", "Ventas netas", "Reservas", "Viajeros"],
            [(m["etiqueta"], m["ventas"], m["reservas"], m["viajeros"]) for m in report["ventas_por_mes"]],
            money_cols=(2,),
        )
        if last > 1:
            chart = BarChart()
            chart.title = "Ventas netas por mes"
            chart.y_axis.title = "COP"
            chart.add_data(Reference(months, min_col=2, min_row=1, max_row=last), titles_from_data=True)
            chart.set_categories(Reference(months, min_col=1, min_row=2, max_row=last))
            chart.width, chart.height = 22, 10
            months.add_chart(chart, "F2")

        # Estados + torta
        states = workbook.create_sheet("Reservas por estado")
        last = table(states, 1, ["Estado", "Reservas"], [(s["etiqueta"], s["total"]) for s in report["reservas_por_estado"]])
        if last > 1:
            pie = PieChart()
            pie.title = "Reservas por estado"
            pie.add_data(Reference(states, min_col=2, min_row=1, max_row=last), titles_from_data=True)
            pie.set_categories(Reference(states, min_col=1, min_row=2, max_row=last))
            states.add_chart(pie, "D2")

        top = workbook.create_sheet("Top paquetes")
        table(top, 1, ["Paquete", "Ventas netas", "Reservas", "Viajeros"],
              [(p["paquete"], p["ventas"], p["reservas"], p["viajeros"]) for p in report["top_paquetes"]], money_cols=(2,))
        top.column_dimensions["A"].width = 40

        cities = workbook.create_sheet("Por destino")
        table(cities, 1, ["Destino", "Ventas netas", "Reservas"],
              [(c["destino"], c["ventas"], c["reservas"]) for c in report["por_destino"]], money_cols=(2,))

        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    # ---------------------------------------------------------------
    # PDF
    # ---------------------------------------------------------------

    def to_pdf(self, report) -> bytes:
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setTitle("Reporte Travelers")
        width, height = A4
        margin = 16 * mm
        night = colors.HexColor("#0b1520")
        orange = colors.HexColor("#f5a524")
        ink = colors.HexColor("#1d2733")
        muted = colors.HexColor("#6b7785")

        pdf.setFillColor(night)
        pdf.rect(0, height - 34 * mm, width, 34 * mm, stroke=0, fill=1)
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(margin, height - 17 * mm, "REPORTE DE OPERACIÓN")
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.HexColor("#c9d2db"))
        pdf.drawString(margin, height - 25 * mm,
                       f"Travelers · del {report['desde']:%d/%m/%Y} al {report['hasta']:%d/%m/%Y}")

        # Tarjetas de indicadores (2 filas x 4)
        k = report["kpis"]
        cards = [
            ("Ventas netas", money(k["ventas_netas"])),
            ("Margen", money(k["margen"])),
            ("Reservas", str(k["reservas"])),
            ("Viajeros", str(k["viajeros"])),
            ("Ticket promedio", money(k["ticket_promedio"])),
            ("Cancelación", f"{k['tasa_cancelacion']} %"),
            ("Cupones", money(k["descuentos_cupones"])),
            ("Calificación", f"{k['calificacion_promedio']} ★" if k["calificacion_promedio"] else "—"),
        ]
        card_w = (width - 2 * margin - 3 * 4 * mm) / 4
        card_h = 18 * mm
        top_y = height - 42 * mm - card_h
        for index, (label, value) in enumerate(cards):
            row, col = divmod(index, 4)
            x = margin + col * (card_w + 4 * mm)
            y = top_y - row * (card_h + 4 * mm)
            pdf.setFillColor(orange if index == 0 else colors.HexColor("#f2f4f7"))
            pdf.roundRect(x, y, card_w, card_h, 3 * mm, stroke=0, fill=1)
            pdf.setFillColor(night if index == 0 else muted)
            pdf.setFont("Helvetica", 8)
            pdf.drawString(x + 4 * mm, y + card_h - 6 * mm, label.upper())
            pdf.setFillColor(night if index == 0 else ink)
            pdf.setFont("Helvetica-Bold", 13)
            pdf.drawString(x + 4 * mm, y + 4.5 * mm, value)

        # Gráfica de ventas por mes
        chart_top = top_y - card_h - 14 * mm
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(margin, chart_top, "Ventas netas por mes")

        months = report["ventas_por_mes"]
        drawing = Drawing(width - 2 * margin, 62 * mm)
        chart = VerticalBarChart()
        chart.x, chart.y = 14 * mm, 10 * mm
        chart.width, chart.height = width - 2 * margin - 18 * mm, 48 * mm
        chart.data = [[float(m["ventas"]) / 1_000_000 for m in months] or [0]]
        chart.categoryAxis.categoryNames = [m["etiqueta"] for m in months] or [""]
        chart.categoryAxis.labels.fontSize = 6.5
        chart.categoryAxis.labels.angle = 30 if len(months) > 8 else 0
        chart.categoryAxis.labels.dy = -6 if len(months) > 8 else -2
        chart.valueAxis.labels.fontSize = 7
        chart.valueAxis.valueMin = 0
        chart.valueAxis.labelTextFormat = "%.1f"
        chart.bars[0].fillColor = orange
        chart.bars[0].strokeColor = None
        chart.barWidth = 6
        drawing.add(chart)
        drawing.add(String(0, 60 * mm, "Millones COP", fontSize=7, fillColor=muted))
        renderPDF.draw(drawing, pdf, margin, chart_top - 66 * mm)

        # Tablas
        y = chart_top - 76 * mm

        def section(title, headers, rows, widths):
            nonlocal y
            if y < 50 * mm:
                pdf.showPage()
                y = height - 20 * mm
            pdf.setFillColor(ink)
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(margin, y, title)
            y -= 7 * mm
            pdf.setFillColor(night)
            pdf.rect(margin, y - 2 * mm, width - 2 * margin, 7 * mm, stroke=0, fill=1)
            pdf.setFillColor(colors.white)
            pdf.setFont("Helvetica-Bold", 8.5)
            x = margin + 3 * mm
            for header, w in zip(headers, widths):
                pdf.drawString(x, y, header)
                x += w
            y -= 7 * mm
            pdf.setFont("Helvetica", 9)
            for row in rows or [["Sin datos en el periodo"]]:
                if y < 20 * mm:
                    pdf.showPage()
                    y = height - 20 * mm
                    pdf.setFont("Helvetica", 9)
                pdf.setFillColor(ink)
                x = margin + 3 * mm
                for value, w in zip(row, widths):
                    pdf.drawString(x, y, str(value)[:46])
                    x += w
                y -= 6 * mm
            y -= 6 * mm

        section("Paquetes más vendidos", ["Paquete", "Ventas netas", "Reservas", "Viajeros"],
                [(p["paquete"], money(p["ventas"]), p["reservas"], p["viajeros"]) for p in report["top_paquetes"]],
                [92 * mm, 36 * mm, 24 * mm, 24 * mm])
        section("Ventas por destino", ["Destino", "Ventas netas", "Reservas"],
                [(c["destino"], money(c["ventas"]), c["reservas"]) for c in report["por_destino"]],
                [92 * mm, 36 * mm, 24 * mm])
        section("Reservas por estado", ["Estado", "Reservas"],
                [(s["etiqueta"], s["total"]) for s in report["reservas_por_estado"]],
                [92 * mm, 36 * mm])

        pdf.setFillColor(muted)
        pdf.setFont("Helvetica", 7.5)
        pdf.drawString(margin, 10 * mm, f"Generado el {datetime.now():%d/%m/%Y %H:%M} · Ventas netas = pagos aprobados + penalidades retenidas")

        pdf.showPage()
        pdf.save()
        return buffer.getvalue()
