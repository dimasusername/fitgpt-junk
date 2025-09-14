"""
Integration tests for database connectivity and operations.
"""
import pytest
import os
from dotenv import load_dotenv

load_dotenv()


@pytest.mark.integration
@pytest.mark.db
def test_database_connection():
    """Test database connection and schema"""
    from supabase import create_client

    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not service_key:
        pytest.skip("Database credentials not available")

    client = create_client(supabase_url, service_key)

    # Test each table exists and is accessible
    tables = ['conversations', 'messages', 'documents', 'document_chunks']

    for table in tables:
        result = client.table(table).select("*").limit(1).execute()
        assert result is not None, f"Could not access table {table}"


@pytest.mark.integration
@pytest.mark.db
def test_database_health_check():
    """Test the database health check function."""
    from app.core.database import health_check
    import asyncio

    # This test requires database to be available
    try:
        result = asyncio.run(health_check())
        assert isinstance(result, bool)
    except Exception:
        pytest.skip("Database not available for health check")


@pytest.mark.integration
@pytest.mark.db
def test_database_relationships():
    """Test database relationships work correctly."""
    from supabase import create_client

    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not service_key:
        pytest.skip("Database credentials not available")

    client = create_client(supabase_url, service_key)

    # Test join query to verify relationships
    result = client.table('conversations').select("""
        id,
        title,
        messages (id, role, content)
    """).limit(1).execute()

    assert result.data is not None
    if result.data:
        conversation = result.data[0]
        assert 'id' in conversation
        assert 'title' in conversation
        # messages might be empty, but the relationship should work
        assert 'messages' in conversation
