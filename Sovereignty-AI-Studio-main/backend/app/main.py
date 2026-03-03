from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.app_name,
    description="A comprehensive multi-modal AI content generation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to CreativeFlow AI"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/v1/mobile/status")
async def mobile_status():
    """Mobile-friendly status endpoint for iOS/iPhone connectivity."""
    return {
        "status": "online",
        "service": "Sovereignty AI Studio",
        "api_version": "v1",
        "port": 9898,
        "endpoints": {
            "health": "/health",
            "alerts": "/api/v1/alerts",
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "websocket": "/api/v1/alerts/ws/{user_id}",
            "studio": "/api/v1/studio",
            "generation": "/api/v1/generation",
            "media": "/api/v1/media",
            "voice": "/api/v1/voice",
            "avatar": "/api/v1/avatar",
            "music": "/api/v1/music",
            "syntax": "/api/v1/syntax",
            "ble_lidar": "/api/v1/ble",
        },
    }
