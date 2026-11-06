from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint
)

from app.database.base import Base


class TouristPackageImageModel(Base):
    __tablename__ = "imagenes_paquetes"

    id_imagen = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    paquete_id = Column(
        Integer,
        ForeignKey(
            "paquetes_turisticos.id_paquete_turistico",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    s3_key = Column(
        String(500),
        nullable=False
    )

    es_portada = Column(
        Boolean,
        nullable=False,
        default=False
    )

    orden = Column(
        Integer,
        nullable=False,
        default=0
    )

    __table_args__ = (
        UniqueConstraint(
            "paquete_id",
            "s3_key",
            name="uq_imagen_paquete"
        ),
    )