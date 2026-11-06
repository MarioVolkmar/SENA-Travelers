import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.routes.user_routes import router as user_router
from app.routes.client_routes import router as client_router
from app.routes.provider_routes import router as provider_router
from app.routes.product_routes import router as product_router
from app.routes.tourist_package_routes import router as tourist_package_router
from app.routes.tourist_package_image_routes import router as package_image_router
from app.routes.reservation_routes import router as reservation_router
from app.routes.payment_routes import router as payment_router
from app.routes.city_routes import router as city_router
from app.routes.provider_payment_routes import router as provider_payment_router
from app.routes.deletion_routes import router as deletion_router
from app.routes.user_overview_routes import router as user_overview_router
from app.routes.engagement_routes import router as engagement_router
from app.routes.commerce_routes import router as commerce_router
from app.core.audit_middleware import AuditMiddleware
from app.services.reminder_service import reminder_loop, reminders_enabled


load_dotenv()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Recordatorios de viaje automáticos (se desactivan con REMINDERS_ENABLED=false)
    task = None
    if reminders_enabled():
        from app.database.connection import SessionLocal
        task = asyncio.create_task(reminder_loop(SessionLocal))
    yield
    if task is not None:
        task.cancel()


app = FastAPI(
    title="Travelers API",
    description="Backend API for Travelers project",
    version="1.0.0",
    lifespan=lifespan,
)

# Orígenes del frontend que pueden llamar al API.
# En producción: CORS_ORIGINS=https://tudominio.com,https://www.tudominio.com
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"

origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

# Bitácora de acciones de administradores (va por dentro de CORS)
app.add_middleware(AuditMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user_router)
app.include_router(client_router)
app.include_router(provider_router)
app.include_router(product_router)
app.include_router(tourist_package_router)
app.include_router(package_image_router)
app.include_router(reservation_router)
app.include_router(payment_router)
app.include_router(city_router)
app.include_router(provider_payment_router)
app.include_router(deletion_router)
app.include_router(user_overview_router)
app.include_router(engagement_router)
app.include_router(commerce_router)


@app.get("/")
def home():
    return {"message": "Travelers API is running"}


@app.get("/db-test")
def test_database_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "success",
            "message": "Database connection successful with SQLAlchemy ORM"
        }
    except Exception as error:
        return {
            "status": "error",
            "message": "Database connection failed",
            "detail": str(error)
        }
