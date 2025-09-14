"""
Unit tests for health endpoints logic (without HTTP).
"""
import pytest
from datetime import datetime


@pytest.mark.unit
@pytest.mark.asyncio
async def test_liveness_check_function():
    """Test the liveness check function directly."""
    from app.api.endpoints.health import liveness_check

    result = await liveness_check()

    assert result["status"] == "alive"
    assert "timestamp" in result
    assert "uptime" in result
    assert isinstance(result["timestamp"], datetime)


@pytest.mark.unit
def test_health_response_model():
    """Test the health response model."""
    from app.api.endpoints.health import HealthResponse
    from datetime import datetime

    # Test valid health response
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "database": True,
        "details": {"test": "data"}
    }

    response = HealthResponse(**health_data)
    assert response.status == "healthy"
    assert response.database is True
    assert response.version == "1.0.0"
