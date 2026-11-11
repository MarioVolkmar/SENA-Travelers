"""
Límite de intentos fallidos de inicio de sesión (protección contra fuerza bruta).

- Por correo: después de LOGIN_MAX_ATTEMPTS fallos seguidos dentro de la ventana,
  ese correo queda bloqueado LOGIN_LOCK_MINUTES minutos.
- Por IP: un límite más alto, para frenar a quien prueba muchos correos distintos.
- Un inicio de sesión correcto borra los fallos de ese correo.

Los contadores viven en memoria. El servidor corre con un solo proceso
(uvicorn --workers 1), así que todos los intentos pasan por aquí; si algún día
se usan varios procesos, habría que guardarlos en un lugar compartido (Redis).
"""
import math
import os
import threading
import time

MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", 5))
MAX_ATTEMPTS_PER_IP = int(os.getenv("LOGIN_MAX_ATTEMPTS_PER_IP", 20))
WINDOW_SECONDS = int(os.getenv("LOGIN_WINDOW_MINUTES", 15)) * 60
LOCK_SECONDS = int(os.getenv("LOGIN_LOCK_MINUTES", 15)) * 60


class TooManyAttemptsError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        minutes = max(1, math.ceil(retry_after / 60))
        unit = "minuto" if minutes == 1 else "minutos"
        super().__init__(
            f"Demasiados intentos fallidos. Intenta de nuevo en {minutes} {unit} "
            "o recupera tu contraseña."
        )


_lock = threading.Lock()
_failures: dict[str, list[float]] = {}     # clave → momentos de los fallos recientes
_locked_until: dict[str, float] = {}       # clave → hasta cuándo está bloqueada


def _keys(email: str, ip: str | None):
    keys = [(f"email:{(email or '').strip().lower()}", MAX_ATTEMPTS)]
    if ip:
        keys.append((f"ip:{ip}", MAX_ATTEMPTS_PER_IP))
    return keys


def ensure_allowed(email: str, ip: str | None = None):
    """Lanza TooManyAttemptsError si el correo o la IP están bloqueados."""
    now = time.monotonic()
    with _lock:
        waits = [
            _locked_until[key] - now
            for key, _ in _keys(email, ip)
            if _locked_until.get(key, 0) > now
        ]
    if waits:
        raise TooManyAttemptsError(math.ceil(max(waits)))


def register_failure(email: str, ip: str | None = None):
    """Anota un fallo; al llegar al límite bloquea la clave."""
    now = time.monotonic()
    with _lock:
        for key, limit in _keys(email, ip):
            recent = [moment for moment in _failures.get(key, []) if now - moment < WINDOW_SECONDS]
            recent.append(now)
            if len(recent) >= limit:
                _locked_until[key] = now + LOCK_SECONDS
                recent = []
            _failures[key] = recent


def register_success(email: str):
    """Un inicio de sesión correcto limpia los fallos de ese correo."""
    key = _keys(email, None)[0][0]
    with _lock:
        _failures.pop(key, None)
        _locked_until.pop(key, None)


def reset_all():
    """Borra todos los contadores (lo usan las pruebas)."""
    with _lock:
        _failures.clear()
        _locked_until.clear()
