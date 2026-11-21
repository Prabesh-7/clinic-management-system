from contextlib import asynccontextmanager

from asyncpg.exceptions import PostgresError
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.api.routes import router as api_router
from app.db.session import close_database, get_engine


@asynccontextmanager
async def lifespan(application: FastAPI):
    yield
    await close_database()

app = FastAPI(
    title=get_settings().app_name,
    description="REST API for Clinic Management System",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    normalized_errors = []
    for error in exc.errors():
        error_type = error.get("type")
        message = error.get("msg", "Invalid value")

        if error_type == "json_invalid":
            message = (
                "Request body is not valid JSON. Check that every string "
                "is enclosed in double quotes and that all commas are correct."
            )

        normalized_errors.append({
            "field": ".".join(str(part) for part in error.get("loc", ()) if part != "body"),
            "message": message,
            "type": error_type,
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": normalized_errors,
        },
    )


@app.get("/")
async def root():
    return {
        "message": "Clinic Management System API",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    try:
        engine = get_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except (RuntimeError, SQLAlchemyError, PostgresError, OSError, ValueError) as exc:
        settings = get_settings()
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "detail": str(exc) if settings.app_env != "production" else "Database unavailable",
            },
        )