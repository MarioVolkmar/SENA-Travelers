from fastapi import FastAPI
from app.database.connection import DatabaseConnection


app = FastAPI(
    title="Travelers API",
    description="Backend API for Travelers project",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Travelers API is running"
    }


@app.get("/db-test")
def test_database_connection():
    database = DatabaseConnection()
    is_connected = database.test_connection()

    if is_connected:
        return {
            "status": "success",
            "message": "Database connection successful"
        }

    return {
        "status": "error",
        "message": "Database connection failed"
    }