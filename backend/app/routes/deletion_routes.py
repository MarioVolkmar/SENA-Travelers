from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user_model import UserModel
from app.services.deletion_service import DeletionService

# Rutas DELETE de la consola del administrador (se suman a los prefijos existentes)
router = APIRouter(tags=["Admin deletions"])


def run_delete(action):
    try:
        action()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))

    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))

    except ValueError as error:
        # 409: existe, pero tiene datos relacionados que impiden borrarlo
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.delete("/providers/{id_proveedor}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(
    id_proveedor: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Elimina un proveedor rechazado (la cuenta del usuario se conserva como cliente)."""
    return run_delete(lambda: DeletionService(db).delete_provider(id_proveedor, current_user))


@router.delete("/packages/{id_paquete_turistico}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    id_paquete_turistico: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Elimina un paquete sin reservas, con sus fotos y productos asociados."""
    return run_delete(lambda: DeletionService(db).delete_package(id_paquete_turistico, current_user))


@router.delete("/products/{id_producto}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Elimina un producto que no esté en paquetes ni en órdenes de pago."""
    return run_delete(lambda: DeletionService(db).delete_product(id_producto, current_user))


@router.delete("/users/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Elimina un usuario sin reservas (y su perfil de cliente, solicitud y notificaciones)."""
    return run_delete(lambda: DeletionService(db).delete_user(id_usuario, current_user))
