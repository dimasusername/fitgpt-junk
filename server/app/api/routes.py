"""
Main API router that includes all route modules.
"""
from fastapi import APIRouter

from app.api.endpoints import health, files, embeddings, search, agent

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["embeddings"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
# Note: Historical analysis tools are now function-based for agent SDK integration