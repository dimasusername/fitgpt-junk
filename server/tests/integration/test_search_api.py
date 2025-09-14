"""
Integration tests for vector search API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app
from app.services.vector_search import SearchResult


class TestSearchAPI:
    """Integration tests for search API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_search_results(self):
        """Mock search results for testing."""
        return [
            SearchResult(
                chunk_id="chunk-1",
                document_id="doc-1",
                content="Roman legions were highly organized military units consisting of about 5000 soldiers.",
                similarity_score=0.85,
                relevance_score=0.87,
                page_number=15,
                chunk_index=1,
                document_filename="roman_army.pdf",
                document_original_name="Roman Army Structure.pdf",
                metadata={"topic": "military_structure", "keywords": ["legion", "soldiers"]},
                source_attribution="Roman Army Structure.pdf, p. 15 (military_structure)"
            ),
            SearchResult(
                chunk_id="chunk-2",
                document_id="doc-1", 
                content="The centurion was a professional officer who commanded a century of about 80 men.",
                similarity_score=0.78,
                relevance_score=0.82,
                page_number=23,
                chunk_index=2,
                document_filename="roman_army.pdf",
                document_original_name="Roman Army Structure.pdf",
                metadata={"topic": "military_hierarchy", "keywords": ["centurion", "officer"]},
                source_attribution="Roman Army Structure.pdf, p. 23 (military_hierarchy)"
            )
        ]

    def test_vector_search_endpoint(self, client, mock_search_results):
        """Test the main vector search endpoint."""
        with patch('app.services.vector_search.vector_search_service.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_results
            
            response = client.post("/api/search/search", json={
                "query": "Roman legion structure",
                "similarity_threshold": 0.7,
                "max_results": 10,
                "boost_recent_docs": True,
                "boost_page_context": True,
                "include_metadata": True
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "query" in data
            assert "results" in data
            assert "total_results" in data
            assert "search_config" in data
            assert "execution_time_ms" in data
            
            # Verify query
            assert data["query"] == "Roman legion structure"
            assert data["total_results"] == 2
            
            # Verify results
            results = data["results"]
            assert len(results) == 2
            
            # Check first result
            first_result = results[0]
            assert first_result["chunk_id"] == "chunk-1"
            assert first_result["similarity_score"] == 0.85
            assert first_result["relevance_score"] == 0.87
            assert first_result["page_number"] == 15
            assert "Roman Army Structure.pdf" in first_result["source_attribution"]
            assert "metadata" in first_result
            assert first_result["metadata"]["topic"] == "military_structure"

    def test_vector_search_with_document_filter(self, client, mock_search_results):
        """Test vector search with document ID filter."""
        with patch('app.services.vector_search.vector_search_service.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_results[:1]  # Return only first result
            
            response = client.post("/api/search/search", json={
                "query": "Roman legion",
                "document_id": "doc-1",
                "similarity_threshold": 0.7,
                "max_results": 5
            })
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["total_results"] == 1
            assert len(data["results"]) == 1
            
            # Verify the search service was called with document filter
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["document_id"] == "doc-1"

    def test_vector_search_with_multiple_documents(self, client, mock_search_results):
        """Test vector search with multiple document IDs."""
        with patch('app.services.vector_search.vector_search_service.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_results
            
            response = client.post("/api/search/search", json={
                "query": "military structure",
                "document_ids": ["doc-1", "doc-2"],
                "similarity_threshold": 0.6,
                "max_results": 10
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify the search service was called with document IDs filter
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["document_ids"] == ["doc-1", "doc-2"]

    def test_vector_search_without_metadata(self, client, mock_search_results):
        """Test vector search with metadata disabled."""
        with patch('app.services.vector_search.vector_search_service.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_results
            
            response = client.post("/api/search/search", json={
                "query": "Roman legion",
                "include_metadata": False
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify metadata is not included in results
            for result in data["results"]:
                assert "metadata" not in result

    def test_context_search_endpoint(self, client):
        """Test the context search endpoint."""
        mock_context_results = [
            {
                "primary_chunk": {
                    "chunk_id": "chunk-2",
                    "content": "Primary content about Roman legions",
                    "similarity_score": 0.85,
                    "relevance_score": 0.87,
                    "page_number": 15,
                    "source_attribution": "Roman Army.pdf, p. 15"
                },
                "context_chunks": [
                    {"content": "Context before", "chunk_index": 1, "page_number": 15},
                    {"content": "Context after", "chunk_index": 3, "page_number": 15}
                ],
                "full_context": "[Context] Context before\n\n[Primary] Primary content about Roman legions\n\n[Context] Context after"
            }
        ]
        
        with patch('app.services.vector_search.vector_search_service.search_with_context', new_callable=AsyncMock) as mock_context:
            mock_context.return_value = mock_context_results
            
            response = client.post("/api/search/context", json={
                "query": "Roman legion structure",
                "context_window": 1,
                "similarity_threshold": 0.7,
                "max_results": 5
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "query" in data
            assert "context_window" in data
            assert "results" in data
            assert "total_results" in data
            
            assert data["query"] == "Roman legion structure"
            assert data["context_window"] == 1
            assert data["total_results"] == 1
            
            # Verify context result structure
            result = data["results"][0]
            assert "primary_chunk" in result
            assert "context_chunks" in result
            assert "full_context" in result
            assert len(result["context_chunks"]) == 2

    def test_search_statistics_endpoint(self, client):
        """Test the search statistics endpoint."""
        mock_stats = {
            "total_searchable_chunks": 150,
            "ready_documents": 5,
            "average_chunk_length": 850,
            "embedding_dimension": 768,
            "search_algorithm": "pgvector HNSW",
            "similarity_metric": "cosine"
        }
        
        with patch('app.services.vector_search.vector_search_service.get_search_statistics', new_callable=AsyncMock) as mock_stats_func:
            mock_stats_func.return_value = mock_stats
            
            response = client.get("/api/search/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify all expected fields are present
            assert data["total_searchable_chunks"] == 150
            assert data["ready_documents"] == 5
            assert data["average_chunk_length"] == 850
            assert data["embedding_dimension"] == 768
            assert data["search_algorithm"] == "pgvector HNSW"
            assert data["similarity_metric"] == "cosine"

    def test_test_search_endpoint(self, client, mock_search_results):
        """Test the simple test search endpoint."""
        with patch('app.services.vector_search.vector_search_service.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_results
            
            response = client.get("/api/search/test", params={
                "query": "Roman legion",
                "threshold": 0.8,
                "limit": 3
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify simplified response structure
            assert "query" in data
            assert "results" in data
            assert "count" in data
            
            assert data["query"] == "Roman legion"
            assert data["count"] == 2
            
            # Verify simplified result format
            for result in data["results"]:
                assert "content" in result
                assert "similarity_score" in result
                assert "relevance_score" in result
                assert "source" in result
                # Content should be truncated if too long
                assert len(result["content"]) <= 203  # 200 chars + "..."

    def test_rerank_results_endpoint(self, client):
        """Test the rerank results endpoint."""
        with patch('app.core.database.get_supabase') as mock_supabase:
            # Setup mock database response
            mock_client = mock_supabase.return_value
            mock_result = type('MockResult', (), {
                'data': [
                    {
                        "id": "chunk-1",
                        "content": "Content about Roman legions and their organization structure",
                        "document_id": "doc-1",
                        "page_number": 15,
                        "chunk_index": 1
                    },
                    {
                        "id": "chunk-2", 
                        "content": "Information about centurions and military hierarchy",
                        "document_id": "doc-1",
                        "page_number": 23,
                        "chunk_index": 2
                    }
                ]
            })()
            mock_client.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_result
            
            response = client.post("/api/search/rerank", json={
                "query": "Roman military structure",
                "chunk_ids": ["chunk-1", "chunk-2"],
                "boost_factors": {
                    "chunk-1": 1.2,
                    "chunk-2": 0.8
                }
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "query" in data
            assert "reranked_results" in data
            assert "total_results" in data
            
            assert data["query"] == "Roman military structure"
            assert data["total_results"] == 2
            
            # Verify reranked results structure
            for result in data["reranked_results"]:
                assert "chunk_id" in result
                assert "content" in result
                assert "base_score" in result
                assert "boost_factor" in result
                assert "final_score" in result

    def test_search_validation_errors(self, client):
        """Test validation errors for search endpoints."""
        # Test empty query
        response = client.post("/api/search/search", json={
            "query": "",
            "similarity_threshold": 0.7
        })
        assert response.status_code == 422  # Validation error
        
        # Test invalid similarity threshold
        response = client.post("/api/search/search", json={
            "query": "test query",
            "similarity_threshold": 1.5  # > 1.0
        })
        assert response.status_code == 422
        
        # Test invalid max_results
        response = client.post("/api/search/search", json={
            "query": "test query",
            "max_results": 0  # < 1
        })
        assert response.status_code == 422

    def test_search_error_handling(self, client):
        """Test error handling in search endpoints."""
        with patch('app.services.vector_search.vector_search_service.search', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("Database connection failed")
            
            response = client.post("/api/search/search", json={
                "query": "test query",
                "similarity_threshold": 0.7
            })
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Vector search failed" in data["detail"]

    def test_context_search_validation(self, client):
        """Test validation for context search endpoint."""
        # Test invalid context window
        response = client.post("/api/search/context", json={
            "query": "test query",
            "context_window": 10  # > 5
        })
        assert response.status_code == 422
        
        # Test negative context window
        response = client.post("/api/search/context", json={
            "query": "test query", 
            "context_window": -1  # < 0
        })
        assert response.status_code == 422

    def test_search_config_application(self, client, mock_search_results):
        """Test that search configuration is properly applied."""
        with patch('app.services.vector_search.vector_search_service.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_results
            
            response = client.post("/api/search/search", json={
                "query": "Roman legion",
                "similarity_threshold": 0.8,
                "max_results": 5,
                "boost_recent_docs": False,
                "boost_page_context": False,
                "include_metadata": False
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify search config in response
            config = data["search_config"]
            assert config["similarity_threshold"] == 0.8
            assert config["max_results"] == 5
            assert config["boost_recent_docs"] == False
            assert config["boost_page_context"] == False
            assert config["include_metadata"] == False
            
            # Verify config was passed to search service
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            search_config = call_args[1]["config"]
            assert search_config.similarity_threshold == 0.8
            assert search_config.max_results == 5
            assert search_config.boost_recent_docs == False
            assert search_config.boost_page_context == False
            assert search_config.include_metadata == False