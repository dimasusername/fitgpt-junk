"""
Integration tests for embeddings functionality.
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient

from main import app
from app.services.embeddings import embedding_service


class TestEmbeddingsIntegration:
    """Integration tests for embeddings API and service."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service for API tests."""
        with patch('app.api.endpoints.embeddings.embedding_service') as mock:
            yield mock

    def test_embedding_stats_endpoint(self, client, mock_embedding_service):
        """Test embedding stats API endpoint."""
        # Mock stats response
        mock_stats = {
            "total_chunks": 100,
            "chunks_with_embeddings": 80,
            "embedding_coverage": 80.0,
            "documents_ready": 5,
            "embedding_model": "text-embedding-004",
            "embedding_dimension": 768
        }
        mock_embedding_service.get_embedding_stats = AsyncMock(return_value=mock_stats)
        
        # Test API call
        response = client.get("/api/embeddings/stats")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["total_chunks"] == 100
        assert data["embedding_coverage"] == 80.0
        assert data["embedding_model"] == "text-embedding-004"

    def test_similarity_search_endpoint(self, client, mock_embedding_service):
        """Test similarity search API endpoint."""
        # Mock search results
        mock_results = [
            {
                "id": "chunk-1",
                "content": "Ancient Roman military tactics",
                "similarity": 0.85,
                "document_filename": "roman_army.pdf",
                "page_number": 1
            },
            {
                "id": "chunk-2", 
                "content": "Legion organization and structure",
                "similarity": 0.78,
                "document_filename": "roman_army.pdf",
                "page_number": 2
            }
        ]
        mock_embedding_service.similarity_search = AsyncMock(return_value=mock_results)
        
        # Test API call
        search_request = {
            "query": "Roman military",
            "similarity_threshold": 0.7,
            "limit": 10
        }
        response = client.post("/api/embeddings/search", json=search_request)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Roman military"
        assert data["total_results"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["similarity"] == 0.85

    def test_document_search_endpoint(self, client, mock_embedding_service):
        """Test document-specific search endpoint."""
        # Mock search results
        mock_results = [
            {
                "id": "chunk-1",
                "content": "Specific content from document",
                "similarity": 0.90,
                "document_filename": "specific_doc.pdf"
            }
        ]
        mock_embedding_service.similarity_search = AsyncMock(return_value=mock_results)
        
        # Test API call
        document_id = "test-doc-id"
        response = client.get(
            f"/api/embeddings/documents/{document_id}/search",
            params={"query": "test query", "limit": 5}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert len(data["results"]) == 1
        
        # Verify service was called with document_id
        mock_embedding_service.similarity_search.assert_called_once_with(
            query="test query",
            document_id=document_id,
            similarity_threshold=0.7,
            limit=5
        )

    def test_reindex_document_endpoint(self, client):
        """Test document reindexing endpoint."""
        with patch('app.api.endpoints.embeddings.document_processing_service') as mock_service:
            # Mock successful reindexing
            mock_service.regenerate_document_embeddings = AsyncMock(return_value=(True, None))
            
            # Test API call
            document_id = "test-doc-id"
            response = client.post(f"/api/embeddings/documents/{document_id}/reindex")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["document_id"] == document_id
            
            # Verify service was called
            mock_service.regenerate_document_embeddings.assert_called_once_with(document_id)

    def test_reindex_document_failure(self, client):
        """Test document reindexing failure."""
        with patch('app.api.endpoints.embeddings.document_processing_service') as mock_service:
            # Mock failed reindexing
            mock_service.regenerate_document_embeddings = AsyncMock(return_value=(False, "Document not found"))
            
            # Test API call
            document_id = "invalid-doc-id"
            response = client.post(f"/api/embeddings/documents/{document_id}/reindex")
            
            # Verify error response
            assert response.status_code == 400
            data = response.json()
            assert "Document not found" in data["detail"]

    def test_query_embedding_endpoint(self, client, mock_embedding_service):
        """Test query embedding generation endpoint."""
        # Mock embedding response
        mock_embedding = [0.1, 0.2, 0.3] * 256  # 768 dimensions
        mock_embedding_service.generate_query_embedding = AsyncMock(return_value=mock_embedding)
        
        # Test API call
        response = client.post("/api/embeddings/query/embedding?query=test query")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert len(data["embedding"]) == 768
        assert data["dimension"] == 768

    def test_search_validation(self, client):
        """Test search request validation."""
        # Test empty query
        response = client.post("/api/embeddings/search", json={"query": ""})
        assert response.status_code == 422
        
        # Test invalid similarity threshold
        response = client.post("/api/embeddings/search", json={
            "query": "test",
            "similarity_threshold": 1.5
        })
        assert response.status_code == 422
        
        # Test invalid limit
        response = client.post("/api/embeddings/search", json={
            "query": "test",
            "limit": 100
        })
        assert response.status_code == 422

    def test_search_with_optional_parameters(self, client, mock_embedding_service):
        """Test search with all optional parameters."""
        mock_embedding_service.similarity_search = AsyncMock(return_value=[])
        
        # Test with all parameters
        search_request = {
            "query": "Roman military tactics",
            "document_id": "specific-doc-id",
            "similarity_threshold": 0.8,
            "limit": 5
        }
        response = client.post("/api/embeddings/search", json=search_request)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify service was called with all parameters
        mock_embedding_service.similarity_search.assert_called_once_with(
            query="Roman military tactics",
            document_id="specific-doc-id",
            similarity_threshold=0.8,
            limit=5
        )

    @pytest.mark.asyncio
    async def test_embedding_service_initialization(self):
        """Test that embedding service initializes correctly."""
        # This test verifies the service can be imported and initialized
        # without actual API calls
        with patch('app.services.embeddings.genai') as mock_genai:
            with patch('app.services.embeddings.settings') as mock_settings:
                mock_settings.GEMINI_API_KEY = "test-key"
                mock_settings.EMBEDDING_MODEL = "text-embedding-004"
                
                # Should not raise an exception
                from app.services.embeddings import EmbeddingService
                service = EmbeddingService()
                
                assert service.model_name == "text-embedding-004"
                assert service.batch_size == 100
                assert service.rate_limit_delay == 0.1