from fastapi import APIRouter

from app.api.v1 import (
    auth,
    catalog,
    eyewear,
    health,
    pd,
    professionals,
    recommendations,
    referrals,
    screening,
    shops,
    users,
    voice,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(screening.router, prefix="/screening", tags=["Screening"])
api_router.include_router(professionals.router, prefix="/professionals", tags=["Professionals"])
api_router.include_router(referrals.router, prefix="/referrals", tags=["Referrals"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["Catalogue"])
api_router.include_router(eyewear.router, prefix="/eyewear", tags=["Virtual Try-On & Eyewear"])
api_router.include_router(shops.router, prefix="/shops", tags=["Shops"])
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
api_router.include_router(pd.router, prefix="/pd", tags=["Pupillary Distance"])
api_router.include_router(voice.router, prefix="/voice", tags=["Voice Assistant"])

# Visual Acuity canonical aliases for unified client access
acuity_alias_router = APIRouter(
    prefix="/acuity", tags=["Visual Acuity Alias"], include_in_schema=False
)
acuity_alias_router.add_api_route(
    "/history",
    screening.list_acuity_history,
    methods=["GET"],
    response_model=screening.VisualAcuityListResponse,
)
acuity_alias_router.add_api_route(
    "/{assessment_id}",
    screening.get_acuity_assessment_by_id,
    methods=["GET"],
    response_model=screening.VisualAcuityResponse,
)
acuity_alias_router.add_api_route(
    "/tests/{test_id}/next",
    screening.get_adaptive_test_challenge,
    methods=["GET"],
    response_model=screening.OptotypeChallengeResponse,
)
acuity_alias_router.add_api_route(
    "/tests/{test_id}/response",
    screening.submit_adaptive_test_response,
    methods=["POST"],
    response_model=screening.AdaptiveAcuityStepResponse,
)
acuity_alias_router.add_api_route(
    "/tests/{test_id}/complete",
    screening.complete_adaptive_test,
    methods=["POST"],
    response_model=screening.AdaptiveAcuityResultResponse,
)
acuity_alias_router.add_api_route(
    "/tests/{test_id}/cancel",
    screening.cancel_adaptive_test,
    methods=["POST"],
    response_model=screening.AdaptiveAcuityResultResponse,
)
acuity_alias_router.add_api_route(
    "/tests/{test_id}/result",
    screening.get_adaptive_test_result,
    methods=["GET"],
    response_model=screening.AdaptiveAcuityResultResponse,
)
api_router.include_router(acuity_alias_router)
