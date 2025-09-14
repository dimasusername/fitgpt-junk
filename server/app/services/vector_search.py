"""
Enhanced vector similarity search service with configurable thresholds,
result ranking, relevance scoring, and source attribution.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException

# from app.core.database import get_supabase, execute_query  # Temporarily disabled
from app.core.database import get_supabase
from app.services.embeddings import embedding_service

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Enhanced search result with relevance scoring and source attribution."""
    chunk_id: str
    document_id: str
    content: str
    similarity_score: float
    relevance_score: float
    page_number: Optional[int]
    chunk_index: int
    document_filename: str
    document_original_name: str
    metadata: Dict[str, Any]
    source_attribution: str


@dataclass
class SearchConfig:
    """Configuration for vector similarity search."""
    similarity_threshold: float = 0.7
    max_results: int = 10
    boost_recent_docs: bool = True
    boost_page_context: bool = True
    min_content_length: int = 50
    include_metadata: bool = True


class VectorSearchService:
    """Enhanced vector similarity search with advanced ranking and scoring."""

    def __init__(self):
        """Initialize the vector search service."""
        self.default_config = SearchConfig()

    async def search(
        self,
        query: str,
        config: Optional[SearchConfig] = None,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Perform enhanced vector similarity search with configurable parameters.

        Args:
            query: Search query text
            config: Search configuration (uses default if None)
            document_id: Optional single document ID to filter by
            document_ids: Optional list of document IDs to filter by

        Returns:
            List of SearchResult objects with enhanced scoring

        Raises:
            HTTPException: If search fails
        """
        try:
            if not query.strip():
                raise ValueError("Query cannot be empty")

            search_config = config or self.default_config

            # Generate query embedding
            query_embedding = await embedding_service.generate_query_embedding(query)

            # Build the search query with filters
            search_results = await self._execute_vector_search(
                query_embedding=query_embedding,
                config=search_config,
                document_id=document_id,
                document_ids=document_ids
            )

            # Enhance results with relevance scoring and ranking
            enhanced_results = await self._enhance_search_results(
                search_results, query, search_config
            )

            # Apply final ranking and limit results
            final_results = self._rank_and_limit_results(
                enhanced_results, search_config
            )

            logger.info(
                f"Vector search completed: {len(final_results)} results for query '{query[:50]}...'"
            )

            return final_results

        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Vector search failed: {str(e)}"
            )

    async def _execute_vector_search(
        self,
        query_embedding: List[float],
        config: SearchConfig,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Execute the core vector similarity search."""
        try:
            client = get_supabase()

            # Base search query
            query_builder = client.rpc(
                "search_document_chunks",
                {
                    "query_embedding": query_embedding,
                    "similarity_threshold": config.similarity_threshold,
                    "match_count": config.max_results * 2  # Get more results for better ranking
                }
            )

            # Apply document filters
            if document_id:
                query_builder = query_builder.eq("document_id", document_id)
            elif document_ids:
                query_builder = query_builder.in_("document_id", document_ids)

            # Execute search
            result = query_builder.execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Failed to execute vector search: {str(e)}")
            raise

    async def _enhance_search_results(
        self,
        raw_results: List[Dict[str, Any]],
        query: str,
        config: SearchConfig
    ) -> List[SearchResult]:
        """Enhance raw search results with relevance scoring and metadata."""
        try:
            enhanced_results = []

            # Get additional document metadata for scoring
            document_metadata = await self._get_document_metadata(
                [result["document_id"] for result in raw_results]
            )

            for result in raw_results:
                # Skip results that are too short
                if len(result["content"]) < config.min_content_length:
                    continue

                # Calculate relevance score
                relevance_score = await self._calculate_relevance_score(
                    result, query, config, document_metadata
                )

                # Get chunk metadata
                chunk_metadata = await self._get_chunk_metadata(result["id"])

                # Create source attribution
                source_attribution = self._create_source_attribution(
                    result, chunk_metadata
                )

                enhanced_result = SearchResult(
                    chunk_id=result["id"],
                    document_id=result["document_id"],
                    content=result["content"],
                    similarity_score=float(result["similarity"]),
                    relevance_score=relevance_score,
                    page_number=result.get("page_number"),
                    chunk_index=result["chunk_index"],
                    document_filename=result["document_filename"],
                    document_original_name=result["document_original_name"],
                    metadata=chunk_metadata if config.include_metadata else {},
                    source_attribution=source_attribution
                )

                enhanced_results.append(enhanced_result)

            return enhanced_results

        except Exception as e:
            logger.error(f"Failed to enhance search results: {str(e)}")
            raise

    async def _calculate_relevance_score(
        self,
        result: Dict[str, Any],
        query: str,
        config: SearchConfig,
        document_metadata: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate enhanced relevance score based on multiple factors."""
        try:
            base_similarity = float(result["similarity"])
            relevance_score = base_similarity

            # Boost for keyword matches in content
            query_terms = query.lower().split()
            content_lower = result["content"].lower()
            keyword_matches = sum(
                1 for term in query_terms if term in content_lower)
            keyword_boost = min(keyword_matches * 0.1, 0.3)  # Max 30% boost
            relevance_score += keyword_boost

            # Boost for recent documents (if enabled)
            if config.boost_recent_docs:
                doc_meta = document_metadata.get(result["document_id"], {})
                if doc_meta.get("uploaded_at"):
                    # Simple recency boost (newer documents get slight preference)
                    days_old = (datetime.now() - doc_meta["uploaded_at"]).days
                    # Max 10% boost for docs < 30 days
                    recency_boost = max(0, (30 - days_old) / 300)
                    relevance_score += recency_boost

            # Boost for page context (if enabled)
            if config.boost_page_context and result.get("page_number"):
                # Slight boost for chunks from earlier pages (often contain key concepts)
                page_num = result["page_number"]
                if page_num <= 10:  # First 10 pages
                    page_boost = (11 - page_num) * 0.01  # Max 10% boost
                    relevance_score += page_boost

            # Content length normalization (prefer substantial chunks)
            content_length = len(result["content"])
            if content_length > 500:  # Substantial content
                length_boost = min((content_length - 500) /
                                   5000, 0.1)  # Max 10% boost
                relevance_score += length_boost

            # Ensure score stays within reasonable bounds
            relevance_score = min(relevance_score, 1.0)

            return relevance_score

        except Exception as e:
            logger.error(f"Failed to calculate relevance score: {str(e)}")
            return float(result.get("similarity", 0.0))

    async def _get_document_metadata(
        self, document_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Get metadata for documents to assist with relevance scoring."""
        try:
            if not document_ids:
                return {}

            client = get_supabase()
            result = (client.table("documents")
                      .select("id, uploaded_at, size, chunk_count")
                      .in_("id", document_ids)
                      .execute())

            metadata = {}
            for doc in result.data or []:
                metadata[doc["id"]] = {
                    "uploaded_at": datetime.fromisoformat(doc["uploaded_at"].replace("Z", "+00:00")),
                    "size": doc["size"],
                    "chunk_count": doc["chunk_count"]
                }

            return metadata

        except Exception as e:
            logger.error(f"Failed to get document metadata: {str(e)}")
            return {}

    async def _get_chunk_metadata(self, chunk_id: str) -> Dict[str, Any]:
        """Get metadata for a specific chunk."""
        try:
            client = get_supabase()
            result = (client.table("document_chunks")
                      .select("metadata")
                      .eq("id", chunk_id)
                      .single()
                      .execute())

            return result.data.get("metadata", {}) if result.data else {}

        except Exception as e:
            logger.error(
                f"Failed to get chunk metadata for {chunk_id}: {str(e)}")
            return {}

    def _create_source_attribution(
        self, result: Dict[str, Any], metadata: Dict[str, Any]
    ) -> str:
        """Create formatted source attribution string."""
        try:
            doc_name = result.get("document_original_name", result.get(
                "document_filename", "Unknown Document"))
            page_info = f", p. {result['page_number']}" if result.get(
                "page_number") else ""

            # Add topic information if available in metadata
            topic_info = ""
            if metadata.get("topic"):
                topic_info = f" ({metadata['topic']})"

            return f"{doc_name}{page_info}{topic_info}"

        except Exception as e:
            logger.error(f"Failed to create source attribution: {str(e)}")
            return "Unknown Source"

    def _rank_and_limit_results(
        self, results: List[SearchResult], config: SearchConfig
    ) -> List[SearchResult]:
        """Apply final ranking and limit results."""
        try:
            # Sort by relevance score (descending), then by similarity score
            sorted_results = sorted(
                results,
                key=lambda x: (x.relevance_score, x.similarity_score),
                reverse=True
            )

            # Limit to max results
            return sorted_results[:config.max_results]

        except Exception as e:
            logger.error(f"Failed to rank and limit results: {str(e)}")
            return results[:config.max_results]

    async def search_with_context(
        self,
        query: str,
        context_window: int = 1,
        config: Optional[SearchConfig] = None
    ) -> List[Dict[str, Any]]:
        """
        Search with context window to include surrounding chunks.

        Args:
            query: Search query
            context_window: Number of chunks before/after to include
            config: Search configuration

        Returns:
            List of results with context chunks included
        """
        try:
            # Get primary search results
            primary_results = await self.search(query, config)

            if not primary_results or context_window <= 0:
                return [self._format_result_for_context(r) for r in primary_results]

            # Get context chunks for each result
            context_results = []

            for result in primary_results:
                context_chunks = await self._get_context_chunks(
                    result.document_id,
                    result.chunk_index,
                    context_window
                )

                context_result = {
                    "primary_chunk": self._format_result_for_context(result),
                    "context_chunks": context_chunks,
                    "full_context": self._merge_context_content(result, context_chunks)
                }

                context_results.append(context_result)

            return context_results

        except Exception as e:
            logger.error(f"Context search failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Context search failed: {str(e)}"
            )

    async def _get_context_chunks(
        self, document_id: str, chunk_index: int, window_size: int
    ) -> List[Dict[str, Any]]:
        """Get surrounding chunks for context."""
        try:
            client = get_supabase()

            # Get chunks before and after the target chunk
            start_index = max(0, chunk_index - window_size)
            end_index = chunk_index + window_size

            result = (client.table("document_chunks")
                      .select("content, chunk_index, page_number")
                      .eq("document_id", document_id)
                      .gte("chunk_index", start_index)
                      .lte("chunk_index", end_index)
                      # Exclude the primary chunk
                      .neq("chunk_index", chunk_index)
                      .order("chunk_index")
                      .execute())

            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get context chunks: {str(e)}")
            return []

    def _format_result_for_context(self, result: SearchResult) -> Dict[str, Any]:
        """Format search result for context response."""
        return {
            "chunk_id": result.chunk_id,
            "content": result.content,
            "similarity_score": result.similarity_score,
            "relevance_score": result.relevance_score,
            "page_number": result.page_number,
            "source_attribution": result.source_attribution,
            "metadata": result.metadata
        }

    def _merge_context_content(
        self, primary_result: SearchResult, context_chunks: List[Dict[str, Any]]
    ) -> str:
        """Merge primary result with context chunks into full context."""
        try:
            # Sort context chunks by index
            sorted_context = sorted(
                context_chunks, key=lambda x: x["chunk_index"])

            # Build full context
            context_parts = []

            for chunk in sorted_context:
                if chunk["chunk_index"] < primary_result.chunk_index:
                    context_parts.append(f"[Context] {chunk['content']}")

            # Add primary chunk
            context_parts.append(f"[Primary] {primary_result.content}")

            for chunk in sorted_context:
                if chunk["chunk_index"] > primary_result.chunk_index:
                    context_parts.append(f"[Context] {chunk['content']}")

            return "\n\n".join(context_parts)

        except Exception as e:
            logger.error(f"Failed to merge context content: {str(e)}")
            return primary_result.content

    async def get_search_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector search index."""
        try:
            client = get_supabase()

            # Count total chunks with embeddings
            chunks_result = (client.table("document_chunks")
                             .select("*", count="exact")
                             .not_.is_("embedding", "null")
                             .execute())

            chunks_with_embeddings = chunks_result.count or 0

            # Count ready documents
            docs_result = (client.table("documents")
                           .select("*", count="exact")
                           .eq("status", "ready")
                           .execute())

            ready_documents = docs_result.count or 0

            # Get average chunk length
            avg_length_query = """
                SELECT AVG(LENGTH(content)) as avg_length
                FROM document_chunks
                WHERE embedding IS NOT NULL
            """

            # avg_result = await execute_query(avg_length_query)  # Temporarily disabled
            # avg_chunk_length = int(avg_result[0]["avg_length"]) if avg_result else 0
            avg_chunk_length = 500  # Default for now

            return {
                "total_searchable_chunks": chunks_with_embeddings,
                "ready_documents": ready_documents,
                "average_chunk_length": avg_chunk_length,
                "embedding_dimension": 768,
                "search_algorithm": "pgvector HNSW",
                "similarity_metric": "cosine"
            }

        except Exception as e:
            logger.error(f"Failed to get search statistics: {str(e)}")
            return {
                "total_searchable_chunks": 0,
                "ready_documents": 0,
                "average_chunk_length": 0,
                "embedding_dimension": 768,
                "search_algorithm": "pgvector HNSW",
                "similarity_metric": "cosine"
            }


# Global vector search service instance
vector_search_service = VectorSearchService()
