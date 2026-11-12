"""Rutas de notificaciones en la app, favoritos, reseñas y bitácora."""
from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user_model import UserModel
from app.schemas.tourist_package_schema import TouristPackageResponse
from app.services.app_notification_service import AppNotificationService
from app.services.audit_service import AuditService
from app.services.favorite_service import FavoriteService
from app.services.review_service import ReviewService


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

class AppNotificationResponse(BaseModel):
    id_notificacion: int
    tipo: str
    titulo: str
    mensaje: str
    enlace: Optional[str] = None
    leida: bool
    fecha: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AppNotificationList(BaseModel):
    no_leidas: int
    notificaciones: List[AppNotificationResponse]


class ReviewCreate(BaseModel):
    reserva_id: int = Field(..., gt=0)
    calificacion: int = Field(..., ge=1, le=5)
    comentario: Optional[str] = Field(None, max_length=600)


class ReviewStatusUpdate(BaseModel):
    estado: str


class ReviewResponse(BaseModel):
    id_resena: int
    reserva_id: int
    paquete_id: int
    paquete: Optional[str] = None
    calificacion: int
    comentario: Optional[str] = None
    estado: str
    fecha: Optional[datetime] = None
    autor: str
    autor_foto: Optional[str] = None


class PackageReviews(BaseModel):
    promedio: float
    total: int
    distribucion: Dict[str, int]
    resenas: List[ReviewResponse]


class ReviewSummary(BaseModel):
    paquete_id: int
    promedio: float
    total: int


class PendingReview(BaseModel):
    reserva_id: int
    codigo_reserva: str
    paquete_id: int
    paquete: str
    fecha_reserva: date


class AuditChange(BaseModel):
    campo: str
    antes: str
    despues: str


class AuditEntry(BaseModel):
    id_registro: int
    usuario_id: Optional[int] = None
    usuario_nombre: str
    accion: str
    entidad: str
    entidad_id: Optional[int] = None
    descripcion: str
    fecha: Optional[datetime] = None
    cambios: List[AuditChange] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


router = APIRouter()

# ---------------------------------------------------------------
# Notificaciones (campana)
# ---------------------------------------------------------------


@router.get("/notifications/app", response_model=AppNotificationList, tags=["Notifications"])
def my_app_notifications(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return AppNotificationService(db).list_mine(current_user)


@router.patch("/notifications/app/read-all", response_model=AppNotificationList, tags=["Notifications"])
def mark_all_read(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return AppNotificationService(db).mark_all_read(current_user)


@router.patch("/notifications/app/{id_notificacion}/read", response_model=AppNotificationResponse, tags=["Notifications"])
def mark_read(id_notificacion: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        return AppNotificationService(db).mark_read(id_notificacion, current_user)
    except (PermissionError, LookupError) as error:
        handle(error)


# ---------------------------------------------------------------
# Favoritos
# ---------------------------------------------------------------


@router.get("/favorites/", response_model=List[TouristPackageResponse], tags=["Favorites"])
def my_favorites(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return FavoriteService(db).list_packages(current_user)


@router.get("/favorites/ids", response_model=List[int], tags=["Favorites"])
def my_favorite_ids(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return FavoriteService(db).list_ids(current_user)


@router.post("/favorites/{paquete_id}", response_model=List[int], tags=["Favorites"])
def add_favorite(paquete_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        return FavoriteService(db).add(paquete_id, current_user)
    except LookupError as error:
        handle(error)


@router.delete("/favorites/{paquete_id}", response_model=List[int], tags=["Favorites"])
def remove_favorite(paquete_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return FavoriteService(db).remove(paquete_id, current_user)


# ---------------------------------------------------------------
# Reseñas
# ---------------------------------------------------------------


@router.get("/reviews/summary", response_model=List[ReviewSummary], tags=["Reviews"])
def review_summaries(db: Session = Depends(get_db)):
    """Promedio de estrellas por paquete (público)."""
    return ReviewService(db).summaries()


@router.get("/reviews/package/{paquete_id}", response_model=PackageReviews, tags=["Reviews"])
def package_reviews(paquete_id: int, db: Session = Depends(get_db)):
    """Reseñas visibles de un paquete (público)."""
    return ReviewService(db).for_package(paquete_id)


@router.get("/reviews/me", response_model=List[ReviewResponse], tags=["Reviews"])
def my_reviews(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return ReviewService(db).my_reviews(current_user)


@router.get("/reviews/me/pending", response_model=List[PendingReview], tags=["Reviews"])
def my_pending_reviews(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return ReviewService(db).pending_for_me(current_user)


@router.post("/reviews/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, tags=["Reviews"])
def create_review(data: ReviewCreate, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        return ReviewService(db).create(data, current_user)
    except (PermissionError, LookupError, ValueError) as error:
        handle(error)


@router.get("/reviews/", response_model=List[ReviewResponse], tags=["Reviews"])
def all_reviews(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        return ReviewService(db).list_all(current_user)
    except PermissionError as error:
        handle(error)


@router.patch("/reviews/{id_resena}/status", response_model=ReviewResponse, tags=["Reviews"])
def set_review_status(
    id_resena: int,
    data: ReviewStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return ReviewService(db).set_status(id_resena, data.estado, current_user)
    except (PermissionError, LookupError, ValueError) as error:
        handle(error)


# ---------------------------------------------------------------
# Bitácora de administradores
# ---------------------------------------------------------------


@router.get("/audit/", response_model=List[AuditEntry], tags=["Audit"])
def audit_log(
    entidad: Optional[str] = None,
    usuario_id: Optional[int] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    buscar: Optional[str] = Query(None, max_length=80),
    limit: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return AuditService(db).list_entries(current_user, entidad, usuario_id, desde, hasta, buscar, limit)
    except PermissionError as error:
        handle(error)
