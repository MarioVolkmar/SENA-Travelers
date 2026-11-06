from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class FavoriteModel(Base):
    __tablename__ = "favoritos"
    __table_args__ = (UniqueConstraint("usuario_id", "paquete_id", name="uq_favorito_usuario_paquete"),)

    id_favorito = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, index=True)
    paquete_id = Column(
        Integer,
        ForeignKey("paquetes_turisticos.id_paquete_turistico", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fecha = Column(DateTime, nullable=False, server_default=func.now())
