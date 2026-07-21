from sqlalchemy.orm import Session

from app.models.user_model import UserModel
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate

from app.core.security import hash_password, verify_password, create_access_token, create_email_verification_token, verify_email_verification_token

from app.repositories.role_repository import RoleRepository

ADMIN_ROLE_ID = 1
CLIENT_ROLE_ID = 2

class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
        self.role_repository = RoleRepository(db)

    def _get_user_or_raise(self, id_usuario: int):
        user = self.user_repository.find_by_id(id_usuario)

        if user is None:
            raise LookupError("El usuario no existe")

        return user

    def _ensure_admin(self, current_user: UserModel):
        if current_user.rol_id != ADMIN_ROLE_ID:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _ensure_owner_or_admin(self, id_usuario: int, current_user: UserModel):
        is_owner = current_user.id_usuario == id_usuario
        is_admin = current_user.rol_id == ADMIN_ROLE_ID

        if not is_owner and not is_admin:
            raise PermissionError("No tienes permisos para realizar esta acción")

    def _ensure_owner(self, id_usuario: int, current_user: UserModel):
        if current_user.id_usuario != id_usuario:
            raise PermissionError("Solo puedes realizar esta acción sobre tu propia cuenta")

    def _ensure_email_available(self, email: str):
        existing_user = self.user_repository.find_by_email(email)

        if existing_user is not None:
            raise ValueError("Email en uso")

    def _ensure_email_validation(self, user: UserModel):
        if user.verificacion_email != "verificado":
            raise PermissionError("La cuenta aun no ha sido verificada")

    def _ensure_user_active(self, user: UserModel):
        if user.estado != "activo":
            raise PermissionError("El usuario no esta activo")

    def create_user(self, user_data: UserCreate):
        self._ensure_email_available(user_data.email)

        contrasena_hash = hash_password(user_data.password)

        user = UserModel(
            nombre=user_data.nombre,
            email=user_data.email,
            contrasena_hash=contrasena_hash,
            rol_id=CLIENT_ROLE_ID
        )

        created_user = self.user_repository.create_user(user)

        validation_token = create_email_verification_token(data={
            "sub": str(created_user.id_usuario)
        })

        print(f"Verification link: http://127.0.0.1:8000/users/verify-email?token={validation_token}")
        
        return created_user, validation_token
    
    def verify_email(self, token: str):
        id_usuario = verify_email_verification_token(token)

        user = self._get_user_or_raise(id_usuario)

        if user.verificacion_email == "verificado":
            raise ValueError("El correo ya está verificado")

        return self.user_repository.update_verification_email(
            user,
            "verificado"
        )


    def get_user_by_id(self, id_usuario: int, current_user : UserModel):
        self._ensure_admin(current_user)
        return self._get_user_or_raise(id_usuario)

    def list_users(self, current_user : UserModel):
        self._ensure_admin(current_user)
        return self.user_repository.list_users()

    def deactivate_user(self, id_usuario: int, current_user : UserModel):
        self._ensure_owner_or_admin(id_usuario, current_user) 
        user = self._get_user_or_raise(id_usuario)
        self._ensure_user_active(user)

        return self.user_repository.deactivate_user(user)
    
    def activate_user(self, id_usuario: int, current_user : UserModel):
        self._ensure_admin(current_user)
        user = self._get_user_or_raise(id_usuario)
        if user.estado == "activo":
            raise ValueError("El usuario ya está activo")

        return self.user_repository.activate_user(user)
    
    def update_user_role(self, id_usuario, rol_id, current_user: UserModel):
        self._ensure_admin(current_user)
        user = self._get_user_or_raise(id_usuario)
        role = self.role_repository.find_role_by_id(rol_id)
        if role is None:
            raise ValueError("El rol no existe")
        return self.user_repository.update_user_role(user, rol_id)

    def update_name(self, id_usuario, name, current_user : UserModel):
        self._ensure_owner_or_admin(id_usuario, current_user)        
        user = self._get_user_or_raise(id_usuario)
        self._ensure_user_active(user)
        self._ensure_email_validation(user)

        return self.user_repository.update_name(user, name)
    
    def update_email(self, id_usuario, email, current_user : UserModel):
        self._ensure_owner_or_admin(id_usuario, current_user) 
        user = self._get_user_or_raise(id_usuario)
        self._ensure_user_active(user)
        self._ensure_email_validation(user)
        self._ensure_email_available(email)       

        return self.user_repository.update_email(user, email)
    
    def update_password(self, id_usuario, actual_password, new_password, current_user: UserModel):
        self._ensure_owner(id_usuario, current_user)        
        user = self._get_user_or_raise(id_usuario)
        self._ensure_user_active(user)
        self._ensure_email_validation(user)

        if not verify_password(actual_password, user.contrasena_hash):
            raise PermissionError("Credenciales incorrectas")

        changed_password = hash_password(new_password)

        return self.user_repository.update_password(user, changed_password) 
    
    def reset_password_by_admin(self, id_usuario ,new_password, current_user: UserModel):
        self._ensure_admin(current_user)
        user = self._get_user_or_raise(id_usuario)
        return self.user_repository.update_password(user, hash_password(new_password))
    
    def login_user(self, email: str, password: str):
        user = self.user_repository.find_by_email(email)

        if user is None:
            raise PermissionError("Correo o contraseña incorrectos")

        if not verify_password(password, user.contrasena_hash):
            raise PermissionError("Correo o contraseña incorrectos")

        if user.estado != "activo":
            raise PermissionError("El usuario está inactivo")

        if user.verificacion_email != "verificado":
            raise PermissionError("Debe verificar su correo electrónico")

        token = create_access_token(
            data={
                "sub": str(user.id_usuario),
                "rol": user.rol_id
            }
        )

        return {
            "access_token": token,
            "token_type": "Bearer"
        }
    
