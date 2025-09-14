"""
Unit tests for embedding service.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from app.services.embeddings import EmbeddingService, EmbeddingResult


class TestEmbeddingService:
    """Test cases for EmbeddingService."""

    @pytest.fixture
    def mock_genai(self):
        """Mock Google AI client."""
        with patch('app.services.embeddings.genai') as mock:
            yield mock

    @pytest.fixture
    def embedding_service(self, mock_genai):
        """Create embedding service with mocked dependencies."""
        with patch('app.services.embeddings.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = "test-api-key"
            mock_settings.EMBEDDING_MODEL = "text-embedding-004"
            
            service = EmbeddingService()
            return service

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, embedding_service, mock_genai):
        """Test successful embedding generation."""
        # Mock the embedding response
        mock_embedding = [0.1, 0.2, 0.3] * 256  # 768 dimensions
        mock_genai.embed_content.return_value = {
            'embedding': mock_embedding
        }
        
        # Test embedding generation
        result = await embedding_service.generate_embedding("test text")
        
        # Verify result
        assert isinstance(result, EmbeddingResult)
        assert result.text == "test text"
        assert result.embedding == mock_embedding
        assert result.token_count > 0
        
        # Verify API call
        mock_genai.embed_content.assert_called_once_with(
            model="models/text-embedding-004",
            content="test text",
            task_type="retrieval_document"
        )

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, embedding_service):
        """Test embedding generation with empty text."""
        with pytest.raises(Exception):
            await embedding_service.generate_embedding("")

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, embedding_service, mock_genai):
        """Test batch embedding generation."""
        # Mock the embedding responses
        mock_embedding = [0.1, 0.2, 0.3] * 256  # 768 dimensions
        mock_genai.embed_content.return_value = {
            'embedding': mock_embedding
        }
        
        texts = ["text 1", "text 2", "text 3"]
        
        # Test batch generation
        results = await embedding_service.generate_embeddings_batch(texts)
        
        # Verify results
        assert len(results) == 3
        for i, result in enumerate(results):
            assert isinstance(result, EmbeddingResult)
            assert result.text == texts[i]
            assert result.embedding == mock_embedding
        
        # Verify API calls
        assert mock_genai.embed_content.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_query_embedding(self, embedding_service, mock_genai):
        """Test query embedding generation."""
        # Mock the embedding response
        mock_embedding = [0.1, 0.2, 0.3] * 256  # 768 dimensions
        mock_genai.embed_content.return_value = {
            'embedding': mock_embedding
        }
        
        # Test query embedding
        result = await embedding_service.generate_query_embedding("search query")
        
        # Verify result
        assert result == mock_embedding
        
        # Verify API call with query task type
        mock_genai.embed_content.assert_called_once_with(
            model="models/text-embedding-004",
            content="search query",
            task_type="retrieval_query"
        )

    @pytest.mark.asyncio
    async def test_store_embeddings(self, embedding_service):
        """Test embedding storage."""
        # Mock Supabase client
        with patch('app.services.embeddings.get_supabase') as mock_get_supabase:
            mock_client = Mock()
            mock_table = Mock()
            mock_update = Mock()
            mock_eq = Mock()
            
            # Set up mock chain
            mock_get_supabase.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.update.return_value = mock_update
            mock_update.eq.return_value = mock_eq
            mock_eq.execute.return_value = Mock(data=[{"id": "test-id"}])
            
            # Test data
            chunk_data = {"id": "chunk-1", "content": "test content"}
            embedding = [0.1, 0.2, 0.3] * 256
            chunk_embeddings = [(chunk_data, embedding)]
            
            # Test storage
            result = await embedding_service.store_embeddings("doc-1", chunk_embeddings)
            
            # Verify result
            assert result is True
            
            # Verify database calls
            mock_client.table.assert_called_with("document_chunks")
            mock_table.update.assert_called_with({"embedding": embedding})
            mock_update.eq.assert_called_with("id", "chunk-1")

    @pytest.mark.asyncio
    async def test_similarity_search(self, embedding_service, mock_genai):
        """Test vector similarity search."""
        # Mock query embedding
        query_embedding = [0.1, 0.2, 0.3] * 256
        mock_genai.embed_content.return_value = {
            'embedding': query_embedding
        }
        
        # Mock Supabase client
        with patch('app.services.embeddings.get_supabase') as mock_get_supabase:
            mock_client = Mock()
            mock_rpc = Mock()
            
            mock_get_supabase.return_value = mock_client
            mock_client.rpc.return_value = mock_rpc
            mock_rpc.execute.return_value = Mock(data=[
                {
                    "id": "chunk-1",
                    "content": "test content",
                    "similarity": 0.85,
                    "document_filename": "test.pdf"
                }
            ])
            
            # Test search
            results = await embedding_service.similarity_search("test query")
            
            # Verify results
            assert len(results) == 1
            assert results[0]["similarity"] == 0.85
            
            # Verify database call
            mock_client.rpc.assert_called_once_with(
                "search_document_chunks",
                {
                    "query_embedding": query_embedding,
                    "similarity_threshold": 0.7,
                    "match_count": 10
                }
            )

    @pytest.mark.asyncio
    async def test_get_embedding_stats(self, embedding_service):
        """Test embedding statistics retrieval."""
        # Mock Supabase client
        with patch('app.services.embeddings.get_supabase') as mock_get_supabase:
            mock_client = Mock()
            mock_table = Mock()
            mock_select = Mock()
            mock_not = Mock()
            mock_is = Mock()
            
            # Set up mock chain for chunks with embeddings
            mock_get_supabase.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.not_.return_value = mock_not
            mock_not.is_.return_value = mock_is
            mock_is.execute.return_value = Mock(count=50)
            
            # Mock total chunks count
            mock_table.select.return_value.execute.return_value = Mock(count=100)
            
            # Mock documents query
            mock_table.select.return_value.eq.return_value.execute.return_value = Mock(
                data=[{"id": "doc-1"}, {"id": "doc-2"}]
            )
            
            # Test stats
            stats = await embedding_service.get_embedding_stats()
            
            # Verify stats structure
            assert "total_chunks" in stats
            assert "chunks_with_embeddings" in stats
            assert "embedding_coverage" in stats
            assert "embedding_model" in stats
            assert stats["embedding_model"] == "text-embedding-004"

    def test_initialization_without_api_key(self):
        """Test service initialization without API key."""
        with patch('app.services.embeddings.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = ""
            
            with pytest.raises(Exception):
                EmbeddingService()

    @pytest.mark.asyncio
    async def test_batch_processing_with_rate_limiting(self, embedding_service, mock_genai):
        """Test that batch processing respects rate limits."""
        # Mock the embedding response
        mock_embedding = [0.1, 0.2, 0.3] * 256
        mock_genai.embed_content.return_value = {
            'embedding': mock_embedding
        }
        
        # Create a large batch to test rate limiting
        texts = [f"text {i}" for i in range(5)]
        
        # Mock asyncio.sleep to verify rate limiting
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            results = await embedding_service.generate_embeddings_batch(texts)
            
            # Verify results
            assert len(results) == 5
            
            # Verify rate limiting was applied
            assert mock_sleep.call_count >= 4  # Should have delays between requests