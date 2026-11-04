from fastapi import APIRouter

from app.api.v1 import (
    auth,
    catalog,
    health,
    pd,
    professionals,
    recommendations,
    referrals,
    screening,
    shops,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(screening.router, prefix="/screening", tags=["Screening"])
api_router.include_router(professionals.router, prefix="/professionals", tags=["Professionals"])
api_router.include_router(referrals.router, prefix="/referrals", tags=["Referrals"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["Catalogue"])
api_router.include_router(shops.router, prefix="/shops", tags=["Shops"])
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
api_router.include_router(pd.router, prefix="/pd", tags=["Pupillary Distance"])
