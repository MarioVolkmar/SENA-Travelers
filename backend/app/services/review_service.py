from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import clock
from app.core.constants import (
    ADMIN_ROLE_ID,
    RESERVATION_STATUS_CONFIRMED,
    REVIEW_STATUS_HIDDEN,
    REVIEW_STATUS_VISIBLE,
)
from app.core.storage import photo_public_url
from app.models.client_model import ClientModel
from app.models.reservation_model import ReservationModel
from app.models.review_model import ReviewModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.user_model import UserModel


def short_name(nombre: str) -> str:
    """«Mario Volkmar» → «Mario V.» (las reseñas son públicas)."""
    parts = (nombre or "Viajero").split()
    return parts[0] if len(parts) == 1 else f"{parts[0]} {parts[1][0]}."


class ReviewService:
    """Reseñas con estrellas de los paquetes, escritas después del viaje."""

    def __init__(self, db: Session):
        self.db = db

    def _client_or_raise(self, current_user: UserModel):
        client = self.db.query(ClientModel).filter(ClientModel.usuario_id == current_user.id_usuario).first()
        if client is None:
            raise PermissionError("Necesitas un perfil de viajero para dejar reseñas")
        return client

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    # ---------------------------------------------------------------
    # Viajero
    # ---------------------------------------------------------------

    def create(self, data, current_user: UserModel):
        client = self._client_or_raise(current_user)

        reservation = self.db.query(ReservationModel).filter(ReservationModel.id_reserva == data.reserva_id).first()
        if reservation is None:
            raise LookupError("La reserva no existe")
        if reservation.cliente_id != client.id_cliente:
            raise PermissionError("Solo puedes reseñar tus propios viajes")
        if reservation.estado != RESERVATION_STATUS_CONFIRMED:
            raise ValueError("Solo puedes reseñar viajes confirmados")
        if reservation.fecha_reserva >= clock.today():
            raise ValueError("Podrás dejar tu reseña después de la fecha del viaje")

        if self.db.query(ReviewModel).filter(ReviewModel.reserva_id == reservation.id_reserva).first():
            raise ValueError("Ya dejaste una reseña para este viaje")

        comentario = (data.comentario or "").strip() or None
        review = ReviewModel(
            reserva_id=reservation.id_reserva,
            paquete_id=reservation.id_paquete_turistico,
            usuario_id=current_user.id_usuario,
            calificacion=data.calificacion,
            comentario=comentario,
            estado=REVIEW_STATUS_VISIBLE,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return self._serialize(review, current_user, self._package_name(review.paquete_id))

    def pending_for_me(self, current_user: UserModel):
        """Viajes ya realizados que todavía no tienen reseña."""
        client = self.db.query(ClientModel).filter(ClientModel.usuario_id == current_user.id_usuario).first()
        if client is None:
            return []

        reviewed = self.db.query(ReviewModel.reserva_id)
        rows = (
            self.db.query(ReservationModel, TouristPackageModel.nombre)
            .join(TouristPackageModel, TouristPackageModel.id_paquete_turistico == ReservationModel.id_paquete_turistico)
            .filter(
                ReservationModel.cliente_id == client.id_cliente,
                ReservationModel.estado == RESERVATION_STATUS_CONFIRMED,
                ReservationModel.fecha_reserva < clock.today(),
                ~ReservationModel.id_reserva.in_(reviewed),
            )
            .order_by(ReservationModel.fecha_reserva.desc())
            .all()
        )
        return [
            {
                "reserva_id": reservation.id_reserva,
                "codigo_reserva": reservation.codigo_reserva,
                "paquete_id": reservation.id_paquete_turistico,
                "paquete": nombre,
                "fecha_reserva": reservation.fecha_reserva,
            }
            for reservation, nombre in rows
        ]

    def my_reviews(self, current_user: UserModel):
        rows = (
            self.db.query(ReviewModel, TouristPackageModel.nombre)
            .join(TouristPackageModel, TouristPackageModel.id_paquete_turistico == ReviewModel.paquete_id)
            .filter(ReviewModel.usuario_id == current_user.id_usuario)
            .order_by(ReviewModel.id_resena.desc())
            .all()
        )
        return [self._serialize(review, current_user, nombre) for review, nombre in rows]

    # ---------------------------------------------------------------
    # Público
    # ---------------------------------------------------------------

    def for_package(self, paquete_id: int):
        rows = (
            self.db.query(ReviewModel, UserModel)
            .join(UserModel, UserModel.id_usuario == ReviewModel.usuario_id)
            .filter(ReviewModel.paquete_id == paquete_id, ReviewModel.estado == REVIEW_STATUS_VISIBLE)
            .order_by(ReviewModel.id_resena.desc())
            .all()
        )
        reviews = [self._serialize(review, user) for review, user in rows]
        distribution = {str(stars): 0 for stars in range(1, 6)}
        for review, _ in rows:
            distribution[str(review.calificacion)] += 1
        total = len(rows)
        average = round(sum(review.calificacion for review, _ in rows) / total, 1) if total else 0
        return {"promedio": average, "total": total, "distribucion": distribution, "resenas": reviews}

    def summaries(self):
        """Promedio y cantidad de reseñas visibles por paquete (para las tarjetas)."""
        rows = (
            self.db.query(ReviewModel.paquete_id, func.avg(ReviewModel.calificacion), func.count(ReviewModel.id_resena))
            .filter(ReviewModel.estado == REVIEW_STATUS_VISIBLE)
            .group_by(ReviewModel.paquete_id)
            .all()
        )
        return [
            {"paquete_id": paquete_id, "promedio": round(float(average), 1), "total": total}
            for paquete_id, average, total in rows
        ]

    # ---------------------------------------------------------------
    # Administración
    # ---------------------------------------------------------------

    def list_all(self, current_user: UserModel):
        self._ensure_admin(current_user)
        rows = (
            self.db.query(ReviewModel, UserModel, TouristPackageModel.nombre)
            .join(UserModel, UserModel.id_usuario == ReviewModel.usuario_id)
            .join(TouristPackageModel, TouristPackageModel.id_paquete_turistico == ReviewModel.paquete_id)
            .order_by(ReviewModel.id_resena.desc())
            .all()
        )
        result = []
        for review, user, package_name in rows:
            item = self._serialize(review, user, package_name)
            item["autor"] = user.nombre  # el admin ve el nombre completo
            result.append(item)
        return result

    def set_status(self, id_resena: int, estado: str, current_user: UserModel):
        self._ensure_admin(current_user)
        if estado not in (REVIEW_STATUS_VISIBLE, REVIEW_STATUS_HIDDEN):
            raise ValueError("Estado de reseña no válido")
        review = self.db.query(ReviewModel).filter(ReviewModel.id_resena == id_resena).first()
        if review is None:
            raise LookupError("La reseña no existe")
        review.estado = estado
        self.db.commit()
        user = self.db.query(UserModel).filter(UserModel.id_usuario == review.usuario_id).first()
        return self._serialize(review, user, self._package_name(review.paquete_id))

    # ---------------------------------------------------------------

    def _package_name(self, paquete_id: int):
        package = (
            self.db.query(TouristPackageModel.nombre)
            .filter(TouristPackageModel.id_paquete_turistico == paquete_id)
            .first()
        )
        return package[0] if package else None

    @staticmethod
    def _serialize(review: ReviewModel, user: UserModel | None, package_name: str | None = None):
        return {
            "id_resena": review.id_resena,
            "reserva_id": review.reserva_id,
            "paquete_id": review.paquete_id,
            "paquete": package_name,
            "calificacion": review.calificacion,
            "comentario": review.comentario,
            "estado": review.estado,
            "fecha": review.fecha,
            "autor": short_name(user.nombre) if user else "Viajero",
            "autor_foto": photo_public_url(user.foto_url) if user and user.foto_url else None,
        }
