"""
Unit tests for configuration and setup.
"""
import pytest


@pytest.mark.unit
def test_imports():
    """Test that all core modules can be imported."""
    try:
        # Test core modules
        from app.core.config import settings
        from app.core.exceptions import AppException

        # Test API modules
        from app.api.routes import api_router
        from app.api.endpoints.health import router

        # Test main app
        from main import app

        assert settings is not None
        assert AppException is not None
        assert api_router is not None
        assert router is not None
        assert app is not None

    except ImportError as e:
        pytest.fail(f"Import failed: {str(e)}")


@pytest.mark.unit
def test_config():
    """Test configuration loading."""
    from app.core.config import settings

    # Test that required settings are available
    assert settings.PROJECT_NAME
    assert settings.CORS_ORIGINS
    assert settings.MAX_FILE_SIZE > 0
    assert settings.GEMINI_MODEL

    # Test that cors_origins_list is properly parsed
    assert isinstance(settings.cors_origins_list, list)


@pytest.mark.unit
def test_exception_classes():
    """Test custom exception classes."""
    from app.core.exceptions import AppException

    # Test basic exception creation
    exc = AppException("Test error", 400, "Test detail")
    assert exc.message == "Test error"
    assert exc.status_code == 400
    assert exc.detail == "Test detail"
