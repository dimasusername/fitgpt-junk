"""
Embeddings API endpoints for RAG functionality.
"""
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.embeddings import embedding_service
from app.services.document_processor import document_processing_service

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for similarity search."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    document_id: Optional[str] = Field(None, description="Optional document ID to search within")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")


class SearchResponse(BaseModel):
    """Response model for similarity search."""
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    search_time_ms: Optional[float] = None


class EmbeddingStatsResponse(BaseModel):
    """Response model for embedding statistics."""
    total_chunks: int
    chunks_with_embeddings: int
    embedding_coverage: float
    documents_ready: int
    embedding_model: str
    embedding_dimension: int


@router.post("/search", response_model=SearchResponse)
async def similarity_search(request: SearchRequest) -> SearchResponse:
    """
    Perform vector similarity search across documents.
    
    This endpoint uses Google Gemini embeddings to find the most relevant
    document chunks based on semantic similarity to the query.
    """
    try:
        import time
        start_time = time.time()
        
        # Perform similarity search
        results = await embedding_service.similarity_search(
            query=request.query,
            document_id=request.document_id,
            similarity_threshold=request.similarity_threshold,
            limit=request.limit
        )
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=round(search_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Similarity search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/stats", response_model=EmbeddingStatsResponse)
async def get_embedding_stats() -> EmbeddingStatsResponse:
    """
    Get statistics about stored embeddings.
    
    Returns information about embedding coverage, model used,
    and overall system status.
    """
    try:
        stats = await embedding_service.get_embedding_stats()
        
        return EmbeddingStatsResponse(
            total_chunks=stats["total_chunks"],
            chunks_with_embeddings=stats["chunks_with_embeddings"],
            embedding_coverage=stats["embedding_coverage"],
            documents_ready=stats["documents_ready"],
            embedding_model=stats["embedding_model"],
            embedding_dimension=stats["embedding_dimension"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get embedding stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get embedding statistics: {str(e)}"
        )


@router.post("/documents/{document_id}/reindex")
async def reindex_document_embeddings(document_id: str) -> Dict[str, Any]:
    """
    Regenerate embeddings for a specific document.
    
    This endpoint will regenerate all embeddings for the specified document,
    useful if the embedding model has been updated or if there were issues
    during initial processing.
    """
    try:
        success, error_message = await document_processing_service.regenerate_document_embeddings(document_id)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully regenerated embeddings for document {document_id}",
                "document_id": document_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=error_message or "Failed to regenerate embeddings"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reindex document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reindex document embeddings: {str(e)}"
        )


@router.get("/documents/{document_id}/search")
async def search_document(
    document_id: str,
    query: str = Query(..., min_length=1, max_length=1000, description="Search query"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
) -> SearchResponse:
    """
    Search within a specific document using vector similarity.
    
    This endpoint performs semantic search within a single document,
    useful for finding specific information within a particular PDF.
    """
    try:
        import time
        start_time = time.time()
        
        # Perform document-specific search
        results = await embedding_service.similarity_search(
            query=query,
            document_id=document_id,
            similarity_threshold=similarity_threshold,
            limit=limit
        )
        
        search_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            search_time_ms=round(search_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Document search failed for {document_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Document search failed: {str(e)}"
        )


@router.post("/query/embedding")
async def generate_query_embedding(query: str = Query(..., min_length=1, max_length=1000)) -> Dict[str, Any]:
    """
    Generate embedding for a query string.
    
    This endpoint is useful for debugging or for applications that want
    to handle vector search manually.
    """
    try:
        embedding = await embedding_service.generate_query_embedding(query)
        
        return {
            "query": query,
            "embedding": embedding,
            "dimension": len(embedding),
            "model": embedding_service.model_name
        }
        
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate query embedding: {str(e)}"
        )