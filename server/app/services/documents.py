"""
Document management service for database operations.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from supabase import Client

from app.core.database import get_supabase
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing document metadata in database."""

    def __init__(self):
        self.client: Optional[Client] = None

    def _get_client(self) -> Client:
        """Get Supabase client."""
        if self.client is None:
            self.client = get_supabase()
        return self.client

    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create document record in database.

        Args:
            document_data: Document metadata dictionary

        Returns:
            Created document record

        Raises:
            HTTPException: If creation fails
        """
        try:
            client = self._get_client()

            # Prepare document record
            document_record = {
                "id": document_data.get("id", str(uuid.uuid4())),
                "filename": document_data["filename"],
                "original_name": document_data["original_name"],
                "storage_path": document_data["storage_path"],
                "public_url": document_data.get("public_url"),
                "mime_type": document_data["mime_type"],
                "size": document_data["size"],
                "uploaded_at": document_data.get("uploaded_at", datetime.utcnow()).isoformat(),
                "status": document_data.get("status", "processing")
            }

            # Insert document record
            result = client.table("documents").insert(
                document_record).execute()

            if not result.data:
                raise DatabaseError("Failed to create document record")

            created_document = result.data[0]
            logger.info(f"Document record created: {created_document['id']}")

            return created_document

        except Exception as e:
            logger.error(f"Failed to create document record: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create document record: {str(e)}"
            )

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document record or None if not found
        """
        try:
            client = self._get_client()

            result = client.table("documents").select(
                "*").eq("id", document_id).execute()

            if result.data:
                return result.data[0]

            return None

        except Exception as e:
            logger.error(f"Failed to get document: {str(e)}")
            return None

    async def get_document_by_storage_path(self, storage_path: str) -> Optional[Dict[str, Any]]:
        """
        Get document by storage path.

        Args:
            storage_path: Storage path of the document

        Returns:
            Document record or None if not found
        """
        try:
            client = self._get_client()

            result = client.table("documents").select(
                "*").eq("storage_path", storage_path).execute()

            if result.data:
                return result.data[0]

            return None

        except Exception as e:
            logger.error(f"Failed to get document by storage path: {str(e)}")
            return None

    async def list_documents(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all documents with pagination.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List of document records
        """
        try:
            client = self._get_client()

            result = (client.table("documents")
                      .select("*")
                      .order("uploaded_at", desc=True)
                      .range(offset, offset + limit - 1)
                      .execute())

            return result.data or []

        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list documents: {str(e)}"
            )

    async def update_document_status(self, document_id: str, status: str,
                                     chunk_count: Optional[int] = None) -> bool:
        """
        Update document processing status.

        Args:
            document_id: Document UUID
            status: New status ('processing', 'ready', 'error')
            chunk_count: Number of chunks created (optional)

        Returns:
            True if update successful
        """
        try:
            client = self._get_client()

            update_data = {"status": status}
            if chunk_count is not None:
                update_data["chunk_count"] = str(chunk_count)

            result = (client.table("documents")
                      .update(update_data)
                      .eq("id", document_id)
                      .execute())

            if result.data:
                logger.info(
                    f"Document status updated: {document_id} -> {status}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update document status: {str(e)}")
            return False

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document record and associated chunks.

        Args:
            document_id: Document UUID

        Returns:
            True if deletion successful
        """
        try:
            client = self._get_client()

            # Delete associated chunks first
            chunks_result = (client.table("document_chunks")
                             .delete()
                             .eq("document_id", document_id)
                             .execute())

            # Delete document record
            doc_result = (client.table("documents")
                          .delete()
                          .eq("id", document_id)
                          .execute())

            if doc_result.data:
                logger.info(f"Document deleted: {document_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete document: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document: {str(e)}"
            )

    async def get_document_stats(self) -> Dict[str, Any]:
        """
        Get document statistics.

        Returns:
            Dictionary with document statistics
        """
        try:
            client = self._get_client()

            # Get total count
            total_result = client.table("documents").select("*").execute()
            total_count = len(total_result.data) if total_result.data else 0

            # Get status counts
            status_counts = {}
            for status in ["processing", "ready", "error"]:
                result = (client.table("documents")
                          .select("*")
                          .eq("status", status)
                          .execute())
                status_counts[status] = len(result.data) if result.data else 0

            # Get total size
            size_result = client.table("documents").select("size").execute()
            total_size = sum(doc.get("size", 0)
                             for doc in (size_result.data or []))

            return {
                "total_documents": total_count,
                "status_counts": status_counts,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }

        except Exception as e:
            logger.error(f"Failed to get document stats: {str(e)}")
            return {
                "total_documents": 0,
                "status_counts": {"processing": 0, "ready": 0, "error": 0},
                "total_size_bytes": 0,
                "total_size_mb": 0
            }


# Global document service instance
document_service = DocumentService()
