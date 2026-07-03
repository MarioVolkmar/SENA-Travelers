from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.routes.user_routes import router as user_router


app = FastAPI(
    title="Travelers API",
    description="Backend API for Travelers project",
    version="1.0.0"
)


app.include_router(user_router)


@app.get("/")
def home():
    return {
        "message": "Travelers API is running"
    }


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