from fastapi import APIRouter
from app.api.v1.endpoints import test, auth, users

api_router = APIRouter()

# Include endpoints
api_router.include_router(test.router, prefix="/test", tags=["test"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])


@api_router.get("/status")
async def api_status():
    return {"status": "API v1 is running"}
