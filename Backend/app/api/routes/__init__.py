from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.admin import router as admin_router
from app.api.routes.clinic import router as clinic_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(clinic_router)
