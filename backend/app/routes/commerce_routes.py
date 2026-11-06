"""Rutas de cupones, voucher con QR, recordatorios y reportes."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user_model import UserModel
from app.services.coupon_service import CouponService
from app.services.reminder_service import ReminderService
from app.services.report_service import ReportService
from app.services.reservation_service import ReservationService
from app.services.voucher_service import VoucherService


def handle(error: Exception):
    if isinstance(error, PermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    if isinstance(error, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    raise error


# ---------------------------------------------------------------
# Esquemas
# ---------------------------------------------------------------

class CouponBase(BaseModel):
    descripcion: Optional[str] = Field(None, max_length=150)
    tipo: Literal["porcentaje", "valor"]
    valor: Decimal = Field(..., gt=0)
    fecha_inicio: date
    fecha_fin: date
    usos_maximos: Optional[int] = Field(None, ge=1)
    monto_minimo: Optional[Decimal] = Field(None, ge=0)


class CouponCreate(CouponBase):
    codigo: str = Field(..., min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    estado: Literal["activo", "inactivo"] = "activo"


class CouponUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    descripcion: Optional[str] = Field(None, max_length=150)
    tipo: Optional[Literal["porcentaje", "valor"]] = None
    valor: Optional[Decimal] = Field(None, gt=0)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    usos_maximos: Optional[int] = Field(None, ge=1)
    monto_minimo: Optional[Decimal] = Field(None, ge=0)
    estado: Optional[Literal["activo", "inactivo"]] = None


class CouponResponse(BaseModel):
    id_cupon: int
    codigo: str
    descripcion: Optional[str] = None
    tipo: str
    valor: Decimal
    fecha_inicio: date
    fecha_fin: date
    usos_maximos: Optional[int] = None
    usos: int
    monto_minimo: Optional[Decimal] = None
    estado: str
    fecha_creacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CouponValidate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=30)
    id_paquete_turistico: int = Field(..., gt=0)
    cantidad_personas: int = Field(..., gt=0, le=50)


class CouponPreview(BaseModel):
    codigo: str
    descripcion: Optional[str] = None
    tipo: str
    valor: Decimal
    subtotal: Decimal
    descuento: Decimal
    total: Decimal


class VoucherVerification(BaseModel):
    codigo_reserva: str
    estado: str
    valida: bool
    paquete: str
    destino: str
    fecha_reserva: date
    cantidad_personas: int
    titular: str


class ReminderRun(BaseModel):
    enviados: int


router = APIRouter()

# ---------------------------------------------------------------
# Cupones
# ---------------------------------------------------------------


@router.post("/coupons/validate", response_model=CouponPreview, tags=["Coupons"])
def validate_coupon(data: CouponValidate, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    """Calcula el descuento de un cupón para un paquete antes de reservar."""
    try:
        return CouponService(db).validate_for_package(
            data.codigo,
            data.id_paquete_turistico,
            data.cantidad_personas,
            ReservationService(db)._calculate_total,
        )
    except (LookupError, ValueError) as error:
        handle(error)


@router.get("/coupons/", response_model=List[CouponResponse], tags=["Coupons"])
def list_coupons(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        return CouponService(db).list_coupons(current_user)
    except PermissionError as error:
        handle(error)


@router.post("/coupons/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED, tags=["Coupons"])
def create_coupon(data: CouponCreate, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        return CouponService(db).create(data.model_dump(), current_user)
    except (PermissionError, ValueError) as error:
        handle(error)


@router.patch("/coupons/{id_cupon}", response_model=CouponResponse, tags=["Coupons"])
def update_coupon(
    id_cupon: int,
    data: CouponUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return CouponService(db).update(id_cupon, data.model_dump(exclude_unset=True), current_user)
    except (PermissionError, LookupError, ValueError) as error:
        handle(error)


@router.delete("/coupons/{id_cupon}", status_code=status.HTTP_204_NO_CONTENT, tags=["Coupons"])
def delete_coupon(id_cupon: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        CouponService(db).delete(id_cupon, current_user)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    except (PermissionError, LookupError) as error:
        handle(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------
# Voucher con QR
# ---------------------------------------------------------------


@router.get("/vouchers/verify/{codigo}", response_model=VoucherVerification, tags=["Vouchers"])
def verify_voucher(codigo: str, db: Session = Depends(get_db)):
    """Lo que abre el QR del voucher: confirma que la reserva existe y su estado (público)."""
    try:
        return VoucherService(db).verify(codigo)
    except LookupError as error:
        handle(error)


@router.get("/vouchers/{id_reserva}", tags=["Vouchers"], response_class=Response)
def download_voucher(id_reserva: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        content, filename = VoucherService(db).build_pdf(id_reserva, current_user)
    except (PermissionError, LookupError, ValueError) as error:
        handle(error)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------
# Recordatorios
# ---------------------------------------------------------------


@router.post("/reminders/run", response_model=ReminderRun, tags=["Reminders"])
def run_reminders(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    """Envía ya los recordatorios pendientes (normalmente se envían solos cada hora)."""
    try:
        return {"enviados": ReminderService(db).run_now(current_user)}
    except PermissionError as error:
        handle(error)


# ---------------------------------------------------------------
# Reportes
# ---------------------------------------------------------------


@router.get("/reports/summary", tags=["Reports"])
def report_summary(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return ReportService(db).build(current_user, desde, hasta)
    except (PermissionError, ValueError) as error:
        handle(error)


@router.get("/reports/export", tags=["Reports"], response_class=Response)
def report_export(
    formato: Literal["xlsx", "pdf"] = "xlsx",
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    service = ReportService(db)
    try:
        report = service.build(current_user, desde, hasta)
    except (PermissionError, ValueError) as error:
        handle(error)

    suffix = f"{report['desde']:%Y%m%d}-{report['hasta']:%Y%m%d}"
    if formato == "pdf":
        content, media = service.to_pdf(report), "application/pdf"
    else:
        content = service.to_excel(report)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="reporte-travelers-{suffix}.{formato}"'},
    )
