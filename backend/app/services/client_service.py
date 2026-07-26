from sqlalchemy.orm import Session

from app.models.client_model import ClientModel
from app.models.user_model import UserModel
from app.repositories.client_repository import ClientRepository
from app.repositories.city_repository import CityRepository
from app.schemas.client_schema import ClientCreate

ADMIN_ROLE_ID = 1
CLIENT_ROLE_ID = 2

class ClientService:
    def __init__(self, db: Session):
        self.client_repository = ClientRepository(db)
        self.city_repository = CityRepository(db)

    def _get_client_or_raise_by_id_client(self, id_cliente: int):
        client = self.client_repository.find_by_id(id_cliente)

        if client is None:
            raise LookupError("El cliente no existe")

        return client

    def _get_client_or_raise_by_id_user(self, id_usuario: int):
        client = self.client_repository.find_by_user_id(id_usuario)
    
        if client is None:
            raise LookupError("El cliente no existe")
    
        return client

    def _ensure_identification_available(self, identificacion: str):
        client = self.client_repository.find_by_identification(identificacion)

        if client is not None:       
            raise ValueError("La identificación ya está registrada")                                          

    def _ensure_city_exist(self, ciudad_id: int):
        city = self.city_repository.find_by_id(ciudad_id)

        if city is None:
            raise ValueError("La ciudad no existe")

    def _ensure_user_is_client(self, user: UserModel):
        if user.rol_id != CLIENT_ROLE_ID:
            raise PermissionError("Solo los usuarios cliente pueden crear perfil de cliente")

    def _ensure_user_email_verified(self, user: UserModel):
        if user.verificacion_email != "verificado":
            raise PermissionError("Debes verificar tu correo antes de crear un perfil de cliente")

    def _ensure_user_has_no_client_profile(self, usuario_id: int):
        client = self.client_repository.find_by_user_id(usuario_id)

        if client is not None:
            raise ValueError("El usuario ya tiene perfil de cliente")

    def _ensure_admin(self, user: UserModel):
        if user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _ensure_owner_or_admin(self, client: ClientModel, current_user: UserModel):
        is_owner = client.usuario_id == current_user.id_usuario
        is_admin = current_user.rol_id == ADMIN_ROLE_ID

        if not is_owner and not is_admin:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def create_client(self, client_data: ClientCreate, current_user: UserModel):
        self._ensure_user_is_client(current_user)
        self._ensure_user_email_verified(current_user)
        self._ensure_user_has_no_client_profile(current_user.id_usuario)
        self._ensure_identification_available(client_data.identificacion)
        self._ensure_city_exist(client_data.ciudad_id)
        
        client = ClientModel(
            usuario_id = current_user.id_usuario,
            identificacion = client_data.identificacion,
            fecha_nacimiento = client_data.fecha_nacimiento,
            ciudad_id = client_data.ciudad_id
        )

        return self.client_repository.create_client(client)

    def get_client_by_id(self, id_cliente: int, current_user: UserModel):
        self._ensure_admin(current_user)
        return self._get_client_or_raise_by_id_client(id_cliente)
    
    def get_client_by_id_user(self, id_usuario: int, current_user: UserModel):
        self._ensure_admin(current_user)
        return self._get_client_or_raise_by_id_user(id_usuario)

    def get_self_client(self, current_user: UserModel):
        self._ensure_user_is_client(current_user)
        return self._get_client_or_raise_by_id_user(current_user.id_usuario)

    def update_client_city(self, cliente_id: int, id_ciudad: int, current_user: UserModel):
        client = self._get_client_or_raise_by_id_client(cliente_id)
        self._ensure_owner_or_admin(client, current_user)
        self._ensure_city_exist(id_ciudad)

        return self.client_repository.update_city_client(client, id_ciudad)

    def list_clients(self, current_user: UserModel):
        self._ensure_admin(current_user)
        return self.client_repository.list_clients()

    