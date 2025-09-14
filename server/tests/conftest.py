"""
Pytest configuration and shared fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add server root to path
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root))


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    from main import app
    return TestClient(app)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "user_id": "test-user-123",
        "conversation_id": "test-conv-456"
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "role": "user",
        "content": "Tell me about Roman military tactics",
        "conversation_id": "test-conv-456"
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "title": "Ancient Roman Military",
        "content": "The Roman army was highly organized...",
        "filename": "roman_military.pdf",
        "file_size": 1024
    }
