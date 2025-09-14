"""
Database connection and initialization.
"""
import logging
from typing import Optional

from supabase import create_client, Client
from supabase.client import ClientOptions

from app.core.config import settings
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

# Global Supabase client
supabase_client: Optional[Client] = None


async def init_db() -> None:
    """Initialize database connections."""
    global supabase_client

    try:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise DatabaseError(
                "Missing Supabase configuration",
                detail="SUPABASE_URL and SUPABASE_SERVICE_KEY are required"
            )

        # Create Supabase client with service key for backend operations
        supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY,
            options=ClientOptions(
                postgrest_client_timeout=10,
                storage_client_timeout=10
            )
        )

        # Test Supabase connection
        try:
            # Try to access a table to test the connection
            conversations = supabase_client.table("conversations")
            conversations.select("*").limit(1).execute()
            logger.info("Supabase connection established successfully")
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            # Still allow initialization to continue for deployment

        logger.info("Database initialization completed")

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise DatabaseError(
            "Failed to connect to database",
            detail=str(e)
        )


async def close_db() -> None:
    """Close database connections."""
    global supabase_client

    # Supabase client doesn't need explicit closing
    supabase_client = None
    logger.info("Database connections closed")


def get_supabase() -> Client:
    """Get Supabase client."""
    if supabase_client is None:
        raise DatabaseError("Database not initialized")
    return supabase_client


async def health_check() -> bool:
    """Check database health."""
    try:
        if supabase_client is None:
            return False

        # Test Supabase connection by trying to access a table
        supabase_client.table("conversations").select("*").limit(1).execute()
        return True

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False
