"""
Document chunk management service for database operations.
"""
import logging
import uuid
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from supabase import Client

from app.core.database import get_supabase
from app.core.exceptions import DatabaseError
from app.services.pdf_processor import DocumentChunk

logger = logging.getLogger(__name__)


class ChunkService:
    """Service for managing document chunks in database."""

    def __init__(self):
        self.client: Optional[Client] = None

    def _get_client(self) -> Client:
        """Get Supabase client."""
        if self.client is None:
            self.client = get_supabase()
        return self.client

    async def store_chunks(self, document_id: str, chunks: List[DocumentChunk]) -> bool:
        """
        Store document chunks in database.
        
        Args:
            document_id: Document UUID
            chunks: List of DocumentChunk objects
            
        Returns:
            True if storage successful
            
        Raises:
            HTTPException: If storage fails
        """
        try:
            client = self._get_client()
            
            # Prepare chunk records for batch insert
            chunk_records = []
            for chunk in chunks:
                chunk_record = {
                    "id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "metadata": {
                        **chunk.metadata,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                        "chunk_size": len(chunk.content)
                    }
                }
                chunk_records.append(chunk_record)
            
            # Batch insert chunks
            if chunk_records:
                result = client.table("document_chunks").insert(chunk_records).execute()
                
                if not result.data:
                    raise DatabaseError("Failed to store document chunks")
                
                logger.info(f"Stored {len(chunk_records)} chunks for document {document_id}")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store chunks for document {document_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store document chunks: {str(e)}"
            )

    async def get_chunks_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            List of chunk records
        """
        try:
            client = self._get_client()
            
            result = (client.table("document_chunks")
                     .select("*")
                     .eq("document_id", document_id)
                     .order("chunk_index")
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get chunks for document {document_id}: {str(e)}")
            return []

    async def delete_chunks_by_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            True if deletion successful
        """
        try:
            client = self._get_client()
            
            result = (client.table("document_chunks")
                     .delete()
                     .eq("document_id", document_id)
                     .execute())
            
            logger.info(f"Deleted chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {str(e)}")
            return False

    async def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get chunk by ID.
        
        Args:
            chunk_id: Chunk UUID
            
        Returns:
            Chunk record or None if not found
        """
        try:
            client = self._get_client()
            
            result = (client.table("document_chunks")
                     .select("*")
                     .eq("id", chunk_id)
                     .execute())
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {str(e)}")
            return None

    async def get_chunk_stats(self, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get chunk statistics.
        
        Args:
            document_id: Optional document ID to filter by
            
        Returns:
            Dictionary with chunk statistics
        """
        try:
            client = self._get_client()
            
            query = client.table("document_chunks").select("*", count="exact")
            
            if document_id:
                query = query.eq("document_id", document_id)
            
            result = query.execute()
            
            total_chunks = result.count or 0
            chunks_data = result.data or []
            
            # Calculate content statistics
            total_chars = sum(len(chunk.get("content", "")) for chunk in chunks_data)
            avg_chunk_size = total_chars / total_chunks if total_chunks > 0 else 0
            
            # Get page distribution
            page_counts = {}
            for chunk in chunks_data:
                page_num = chunk.get("page_number", 0)
                page_counts[page_num] = page_counts.get(page_num, 0) + 1
            
            stats = {
                "total_chunks": total_chunks,
                "total_characters": total_chars,
                "average_chunk_size": round(avg_chunk_size, 2),
                "pages_with_chunks": len(page_counts),
                "chunks_per_page": dict(sorted(page_counts.items())) if page_counts else {}
            }
            
            if document_id:
                stats["document_id"] = document_id
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get chunk stats: {str(e)}")
            return {
                "total_chunks": 0,
                "total_characters": 0,
                "average_chunk_size": 0,
                "pages_with_chunks": 0,
                "chunks_per_page": {}
            }

    async def search_chunks_by_content(self, query: str, document_id: Optional[str] = None, 
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search chunks by content (basic text search).
        
        Args:
            query: Search query
            document_id: Optional document ID to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching chunk records
        """
        try:
            client = self._get_client()
            
            # Use PostgreSQL text search
            search_query = client.table("document_chunks").select("*")
            
            if document_id:
                search_query = search_query.eq("document_id", document_id)
            
            # Use ilike for case-insensitive search
            search_query = (search_query
                           .ilike("content", f"%{query}%")
                           .order("chunk_index")
                           .limit(limit))
            
            result = search_query.execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to search chunks: {str(e)}")
            return []


# Global chunk service instance
chunk_service = ChunkService()