"""
Google Gemini embeddings service for RAG pipeline.
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import google.generativeai as genai
from fastapi import HTTPException

from app.core.config import settings
from app.core.database import get_supabase
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    text: str
    embedding: List[float]
    token_count: int


class EmbeddingService:
    """Service for generating and managing text embeddings using Google Gemini."""

    def __init__(self):
        """Initialize the embedding service."""
        self.client = None
        self.model_name = settings.EMBEDDING_MODEL
        self.batch_size = 100  # Process embeddings in batches
        self.rate_limit_delay = 0.1  # 100ms delay between requests
        self._setup_client()

    def _setup_client(self):
        """Set up Google AI client with authentication."""
        try:
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is required for embedding generation")
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            logger.info(f"Initialized Google AI client for embeddings with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google AI client: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize embedding service: {str(e)}"
            )

    async def generate_embedding(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            EmbeddingResult with text, embedding vector, and token count
            
        Raises:
            HTTPException: If embedding generation fails
        """
        try:
            if not text.strip():
                raise ValueError("Text cannot be empty")
            
            # Use Google's embedding model
            result = genai.embed_content(
                model=f"models/{self.model_name}",
                content=text,
                task_type="retrieval_document"  # Optimized for RAG
            )
            
            embedding = result['embedding']
            
            # Estimate token count (rough approximation)
            token_count = len(text.split()) * 1.3  # Rough estimate
            
            return EmbeddingResult(
                text=text,
                embedding=embedding,
                token_count=int(token_count)
            )
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embedding: {str(e)}"
            )

    async def generate_embeddings_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts with rate limiting.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of EmbeddingResult objects
            
        Raises:
            HTTPException: If batch embedding generation fails
        """
        try:
            if not texts:
                return []
            
            results = []
            
            # Process in batches to avoid rate limits
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                batch_results = []
                
                logger.info(f"Processing embedding batch {i//self.batch_size + 1}/{(len(texts) + self.batch_size - 1)//self.batch_size}")
                
                for text in batch:
                    try:
                        result = await self.generate_embedding(text)
                        batch_results.append(result)
                        
                        # Rate limiting delay
                        if self.rate_limit_delay > 0:
                            await asyncio.sleep(self.rate_limit_delay)
                            
                    except Exception as e:
                        logger.error(f"Failed to embed text chunk: {str(e)}")
                        # Continue with other chunks, don't fail the entire batch
                        continue
                
                results.extend(batch_results)
                
                # Longer delay between batches
                if i + self.batch_size < len(texts):
                    await asyncio.sleep(1.0)
            
            logger.info(f"Generated {len(results)} embeddings from {len(texts)} texts")
            return results
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate batch embeddings: {str(e)}"
            )

    async def store_embeddings(self, document_id: str, chunk_embeddings: List[Tuple[Dict[str, Any], List[float]]]) -> bool:
        """
        Store embeddings in Supabase pgvector.
        
        Args:
            document_id: Document UUID
            chunk_embeddings: List of tuples (chunk_data, embedding_vector)
            
        Returns:
            True if storage successful
            
        Raises:
            HTTPException: If storage fails
        """
        try:
            if not chunk_embeddings:
                return True
            
            client = get_supabase()
            
            # Update chunk records with embeddings
            updates = []
            for chunk_data, embedding in chunk_embeddings:
                update_data = {
                    "embedding": embedding
                }
                
                # Update the specific chunk by ID
                result = (client.table("document_chunks")
                         .update(update_data)
                         .eq("id", chunk_data["id"])
                         .execute())
                
                if not result.data:
                    logger.warning(f"Failed to update embedding for chunk {chunk_data['id']}")
                else:
                    updates.append(chunk_data["id"])
            
            logger.info(f"Stored {len(updates)} embeddings for document {document_id}")
            return len(updates) > 0
            
        except Exception as e:
            logger.error(f"Failed to store embeddings for document {document_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store embeddings: {str(e)}"
            )

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            HTTPException: If embedding generation fails
        """
        try:
            if not query.strip():
                raise ValueError("Query cannot be empty")
            
            # Use query-optimized task type
            result = genai.embed_content(
                model=f"models/{self.model_name}",
                content=query,
                task_type="retrieval_query"  # Optimized for search queries
            )
            
            return result['embedding']
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate query embedding: {str(e)}"
            )

    async def similarity_search(self, query: str, document_id: Optional[str] = None, 
                              similarity_threshold: float = 0.7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using pgvector.
        
        Args:
            query: Search query
            document_id: Optional document ID to filter by
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum number of results
            
        Returns:
            List of matching chunks with similarity scores
            
        Raises:
            HTTPException: If search fails
        """
        try:
            # Generate query embedding
            query_embedding = await self.generate_query_embedding(query)
            
            client = get_supabase()
            
            # Use the database function for vector search
            if document_id:
                # Search within specific document
                result = client.rpc(
                    "search_document_chunks",
                    {
                        "query_embedding": query_embedding,
                        "similarity_threshold": similarity_threshold,
                        "match_count": limit
                    }
                ).eq("document_id", document_id).execute()
            else:
                # Search across all documents
                result = client.rpc(
                    "search_document_chunks",
                    {
                        "query_embedding": query_embedding,
                        "similarity_threshold": similarity_threshold,
                        "match_count": limit
                    }
                ).execute()
            
            search_results = result.data or []
            
            logger.info(f"Vector search returned {len(search_results)} results for query: {query[:50]}...")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to perform similarity search: {str(e)}"
            )

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored embeddings.
        
        Returns:
            Dictionary with embedding statistics
        """
        try:
            client = get_supabase()
            
            # Count chunks with embeddings
            result = (client.table("document_chunks")
                     .select("*", count="exact")
                     .not_.is_("embedding", "null")
                     .execute())
            
            chunks_with_embeddings = result.count or 0
            
            # Count total chunks
            total_result = (client.table("document_chunks")
                           .select("*", count="exact")
                           .execute())
            
            total_chunks = total_result.count or 0
            
            # Get documents with embeddings
            doc_result = (client.table("documents")
                         .select("id, filename, chunk_count")
                         .eq("status", "ready")
                         .execute())
            
            documents = doc_result.data or []
            
            return {
                "total_chunks": total_chunks,
                "chunks_with_embeddings": chunks_with_embeddings,
                "embedding_coverage": round(chunks_with_embeddings / total_chunks * 100, 2) if total_chunks > 0 else 0,
                "documents_ready": len(documents),
                "embedding_model": self.model_name,
                "embedding_dimension": 768  # text-embedding-004 dimension
            }
            
        except Exception as e:
            logger.error(f"Failed to get embedding stats: {str(e)}")
            return {
                "total_chunks": 0,
                "chunks_with_embeddings": 0,
                "embedding_coverage": 0,
                "documents_ready": 0,
                "embedding_model": self.model_name,
                "embedding_dimension": 768
            }

    async def reindex_document_embeddings(self, document_id: str) -> bool:
        """
        Regenerate embeddings for all chunks of a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            True if reindexing successful
            
        Raises:
            HTTPException: If reindexing fails
        """
        try:
            client = get_supabase()
            
            # Get all chunks for the document
            result = (client.table("document_chunks")
                     .select("*")
                     .eq("document_id", document_id)
                     .order("chunk_index")
                     .execute())
            
            chunks = result.data or []
            
            if not chunks:
                logger.warning(f"No chunks found for document {document_id}")
                return False
            
            # Extract text content
            texts = [chunk["content"] for chunk in chunks]
            
            # Generate embeddings
            embedding_results = await self.generate_embeddings_batch(texts)
            
            if len(embedding_results) != len(chunks):
                logger.warning(f"Embedding count mismatch: {len(embedding_results)} vs {len(chunks)}")
            
            # Prepare chunk-embedding pairs
            chunk_embeddings = []
            for i, embedding_result in enumerate(embedding_results):
                if i < len(chunks):
                    chunk_embeddings.append((chunks[i], embedding_result.embedding))
            
            # Store embeddings
            success = await self.store_embeddings(document_id, chunk_embeddings)
            
            if success:
                logger.info(f"Successfully reindexed {len(chunk_embeddings)} chunks for document {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reindex embeddings for document {document_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reindex document embeddings: {str(e)}"
            )


# Global embedding service instance
embedding_service = EmbeddingService()