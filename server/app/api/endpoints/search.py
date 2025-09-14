"""
Vector similarity search API endpoints.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.services.vector_search import vector_search_service, SearchConfig, SearchResult

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for vector similarity search."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    max_results: int = Field(10, ge=1, le=50, description="Maximum number of results")
    document_id: Optional[str] = Field(None, description="Optional document ID to filter by")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to filter by")
    boost_recent_docs: bool = Field(True, description="Boost scores for recently uploaded documents")
    boost_page_context: bool = Field(True, description="Boost scores based on page context")
    include_metadata: bool = Field(True, description="Include chunk metadata in results")


class SearchResponse(BaseModel):
    """Response model for vector similarity search."""
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    search_config: Dict[str, Any]
    execution_time_ms: Optional[float] = None


class ContextSearchRequest(BaseModel):
    """Request model for context-aware search."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    context_window: int = Field(1, ge=0, le=5, description="Number of chunks before/after to include")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of results")


class SearchStatsResponse(BaseModel):
    """Response model for search statistics."""
    total_searchable_chunks: int
    ready_documents: int
    average_chunk_length: int
    embedding_dimension: int
    search_algorithm: str
    similarity_metric: str


@router.post("", response_model=SearchResponse)
async def vector_search(request: SearchRequest):
    """
    Perform vector similarity search with configurable parameters.
    
    This endpoint provides enhanced vector similarity search with:
    - Configurable similarity thresholds
    - Advanced relevance scoring and ranking
    - Source attribution with document and page information
    - Optional document filtering
    - Metadata inclusion
    """
    try:
        import time
        start_time = time.time()
        
        # Create search configuration
        config = SearchConfig(
            similarity_threshold=request.similarity_threshold,
            max_results=request.max_results,
            boost_recent_docs=request.boost_recent_docs,
            boost_page_context=request.boost_page_context,
            include_metadata=request.include_metadata
        )
        
        # Perform search
        results = await vector_search_service.search(
            query=request.query,
            config=config,
            document_id=request.document_id,
            document_ids=request.document_ids
        )
        
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Format results for response
        formatted_results = []
        for result in results:
            formatted_result = {
                "chunk_id": result.chunk_id,
                "document_id": result.document_id,
                "content": result.content,
                "similarity_score": round(result.similarity_score, 4),
                "relevance_score": round(result.relevance_score, 4),
                "page_number": result.page_number,
                "chunk_index": result.chunk_index,
                "document_filename": result.document_filename,
                "document_original_name": result.document_original_name,
                "source_attribution": result.source_attribution
            }
            
            if request.include_metadata:
                formatted_result["metadata"] = result.metadata
            
            formatted_results.append(formatted_result)
        
        return SearchResponse(
            query=request.query,
            results=formatted_results,
            total_results=len(formatted_results),
            search_config={
                "similarity_threshold": config.similarity_threshold,
                "max_results": config.max_results,
                "boost_recent_docs": config.boost_recent_docs,
                "boost_page_context": config.boost_page_context,
                "include_metadata": config.include_metadata
            },
            execution_time_ms=round(execution_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Vector search failed: {str(e)}"
        )


@router.post("/context")
async def context_search(request: ContextSearchRequest):
    """
    Perform vector similarity search with context windows.
    
    This endpoint returns search results with surrounding chunks for better context.
    Each result includes the primary matching chunk plus surrounding chunks.
    """
    try:
        # Create search configuration
        config = SearchConfig(
            similarity_threshold=request.similarity_threshold,
            max_results=request.max_results
        )
        
        # Perform context search
        results = await vector_search_service.search_with_context(
            query=request.query,
            context_window=request.context_window,
            config=config
        )
        
        return {
            "query": request.query,
            "context_window": request.context_window,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Context search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Context search failed: {str(e)}"
        )


@router.get("/stats", response_model=SearchStatsResponse)
async def get_search_statistics():
    """
    Get statistics about the vector search index.
    
    Returns information about:
    - Total searchable chunks
    - Ready documents
    - Average chunk length
    - Embedding configuration
    """
    try:
        stats = await vector_search_service.get_search_statistics()
        
        return SearchStatsResponse(
            total_searchable_chunks=stats["total_searchable_chunks"],
            ready_documents=stats["ready_documents"],
            average_chunk_length=stats["average_chunk_length"],
            embedding_dimension=stats["embedding_dimension"],
            search_algorithm=stats["search_algorithm"],
            similarity_metric=stats["similarity_metric"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get search statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get search statistics: {str(e)}"
        )


@router.get("/test")
async def test_search(
    query: str = Query(..., description="Test query"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Similarity threshold"),
    limit: int = Query(5, ge=1, le=20, description="Result limit")
):
    """
    Simple test endpoint for vector search functionality.
    
    Use this endpoint to quickly test vector search with minimal parameters.
    """
    try:
        config = SearchConfig(
            similarity_threshold=threshold,
            max_results=limit
        )
        
        results = await vector_search_service.search(query=query, config=config)
        
        # Return simplified results for testing
        simple_results = []
        for result in results:
            simple_results.append({
                "content": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                "similarity_score": round(result.similarity_score, 3),
                "relevance_score": round(result.relevance_score, 3),
                "source": result.source_attribution
            })
        
        return {
            "query": query,
            "results": simple_results,
            "count": len(simple_results)
        }
        
    except Exception as e:
        logger.error(f"Test search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Test search failed: {str(e)}"
        )


class RerankRequest(BaseModel):
    """Request model for reranking results."""
    query: str = Field(..., description="Original search query")
    chunk_ids: List[str] = Field(..., description="List of chunk IDs to rerank")
    boost_factors: Optional[Dict[str, float]] = Field(None, description="Optional boost factors for specific chunks")


@router.post("/rerank")
async def rerank_results(request: RerankRequest):
    """
    Rerank a set of search results with custom boost factors.
    
    This endpoint allows for custom reranking of search results based on
    additional criteria or user feedback.
    """
    try:
        # This is a simplified reranking implementation
        # In a production system, you might use more sophisticated reranking models
        
        from app.core.database import get_supabase
        
        client = get_supabase()
        
        # Get the chunks
        result = (client.table("document_chunks")
                 .select("id, content, document_id, page_number, chunk_index")
                 .in_("id", request.chunk_ids)
                 .execute())
        
        chunks = result.data or []
        
        # Generate query embedding for similarity calculation
        query_embedding = await vector_search_service.embedding_service.generate_query_embedding(request.query)
        
        # Calculate similarities and apply boost factors
        reranked_results = []
        for chunk in chunks:
            # This is a simplified approach - in practice you'd want to get the actual embeddings
            base_score = 0.8  # Placeholder score
            
            boost_factor = request.boost_factors.get(chunk["id"], 1.0) if request.boost_factors else 1.0
            final_score = base_score * boost_factor
            
            reranked_results.append({
                "chunk_id": chunk["id"],
                "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                "base_score": base_score,
                "boost_factor": boost_factor,
                "final_score": final_score,
                "page_number": chunk.get("page_number")
            })
        
        # Sort by final score
        reranked_results.sort(key=lambda x: x["final_score"], reverse=True)
        
        return {
            "query": request.query,
            "reranked_results": reranked_results,
            "total_results": len(reranked_results)
        }
        
    except Exception as e:
        logger.error(f"Reranking failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Reranking failed: {str(e)}"
        )