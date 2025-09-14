"""
API endpoint tests using FastAPI TestClient.
"""
import pytest


@pytest.mark.api
def test_health_endpoint_via_api(client):
    """Test the main health endpoint via the API"""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data
    assert "version" in data
    assert "database" in data


@pytest.mark.api
def test_liveness_endpoint(client):
    """Test the liveness endpoint"""
    response = client.get("/api/health/live")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert "uptime" in data


@pytest.mark.api
def test_readiness_endpoint(client):
    """Test the readiness endpoint"""
    response = client.get("/api/health/ready")
    # This might return 503 if database is not available, so we check for both
    assert response.status_code in [200, 503]

    data = response.json()
    if response.status_code == 200:
        assert data["status"] == "ready"
        assert "timestamp" in data


@pytest.mark.api
def test_api_docs_available(client):
    """Test that API documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200


@pytest.mark.api
def test_openapi_json(client):
    """Test that OpenAPI JSON is available"""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "AI Chat Application"
