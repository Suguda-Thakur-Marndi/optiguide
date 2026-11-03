from fastapi import APIRouter

from app.api.v1 import auth, health, screening, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(screening.router, prefix="/screening", tags=["Screening"])
