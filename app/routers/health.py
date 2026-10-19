from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }

@router.get("/ready")
async def readiness_check():
    # Will incorporate Redis and upstream connectivity checks in subsequent phases
    return {
        "status": "ready",
        "providers_configured": ["gemini", "groq"]
    }
