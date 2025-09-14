"""
Health check endpoints.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.database import health_check
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    database: bool
    details: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_endpoint():
    """
    Health check endpoint.

    Returns the current health status of the application and its dependencies.
    """
    try:
        # Check database health
        db_healthy = await health_check()

        # Determine overall status
        overall_status = "healthy" if db_healthy else "degraded"

        # Prepare response
        response = HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            database=db_healthy,
            details={
                "database_status": "connected" if db_healthy else "disconnected",
                "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY),
                "gemini_configured": bool(settings.GEMINI_API_KEY),
                "cors_origins": settings.cors_origins_list,
                "max_file_size": settings.MAX_FILE_SIZE,
                "allowed_file_types": settings.ALLOWED_FILE_TYPES
            }
        )

        logger.info(f"Health check completed: {overall_status}")
        return response

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Health check failed"
        )


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint for deployment health checks.

    Returns 200 if the application is ready to serve requests.
    """
    try:
        db_healthy = await health_check()

        if not db_healthy:
            raise HTTPException(
                status_code=503,
                detail="Service not ready - database unavailable"
            )

        return {"status": "ready", "timestamp": datetime.utcnow()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service not ready"
        )


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check endpoint for deployment health checks.

    Returns 200 if the application is alive (basic functionality works).
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow(),
        "uptime": "running"
    }