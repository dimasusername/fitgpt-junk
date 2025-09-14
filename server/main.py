"""
FastAPI main application entry point.
"""
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import api_router
from app.core.exceptions import AppException


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting up application...")

    # Initialize database connection
    await init_db()
    logger.info("Database initialized")

    yield

    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="AI Chat Application",
    description="FastAPI backend for AI chat with RAG capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()

    logger.info(f"Request: {request.method} {request.url}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} - "
        f"Process time: {process_time:.4f}s"
    )

    return response


# Global exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application-specific exceptions."""
    logger.error(f"Application error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "detail": exc.detail}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )


# Include API routes
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    # Get port from environment (Railway sets PORT automatically)
    port = int(os.getenv("PORT", 8000))
    
    # Disable reload in production
    reload = os.getenv("RAILWAY_ENVIRONMENT") != "production"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=reload
    )