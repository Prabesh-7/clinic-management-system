from fastapi import FastAPI

app = FastAPI(
    title="Clinic Management System API",
    description="REST API for Clinic Management System",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "message": "Clinic Management System API",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }