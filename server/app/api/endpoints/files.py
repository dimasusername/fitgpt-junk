"""
File upload and management endpoints.
"""
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Path
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.services.storage import storage_service
from app.services.documents import document_service
from app.services.document_processor import document_processing_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentResponse(BaseModel):
    """Document response model."""
    id: str
    filename: str
    original_name: str
    storage_path: str
    public_url: Optional[str]
    mime_type: str
    size: int
    uploaded_at: datetime
    status: str
    chunk_count: Optional[int] = None


class DocumentListResponse(BaseModel):
    """Document list response model."""
    documents: List[DocumentResponse]
    total: int
    limit: int
    offset: int


class DocumentStatsResponse(BaseModel):
    """Document statistics response model."""
    total_documents: int
    status_counts: dict
    total_size_bytes: int
    total_size_mb: float


class UploadResponse(BaseModel):
    """File upload response model."""
    success: bool
    message: str
    document: Optional[DocumentResponse] = None


class DeleteResponse(BaseModel):
    """File deletion response model."""
    success: bool
    message: str


class ProcessingStatusResponse(BaseModel):
    """Document processing status response model."""
    document_id: str
    status: str
    filename: str
    uploaded_at: datetime
    file_size: int
    chunk_stats: dict


class DocumentPreviewResponse(BaseModel):
    """Document content preview response model."""
    document_id: str
    filename: str
    status: str
    total_chunks: int
    preview_chunks: List[dict]


class ProcessingResponse(BaseModel):
    """Document processing response model."""
    success: bool
    message: str
    document_id: str


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="PDF file to upload")
):
    """
    Upload a PDF file to Supabase Storage.

    - **file**: PDF file (max 25MB)

    Returns document metadata and storage information.
    """
    try:
        logger.info(f"Starting file upload: {file.filename}")

        # Upload file to storage
        file_metadata = await storage_service.upload_file(file)

        # Create document record in database
        document_record = await document_service.create_document(file_metadata)

        # Trigger document processing asynchronously
        document_id = document_record["id"]
        try:
            # Start processing in background (don't wait for completion)
            import asyncio
            asyncio.create_task(
                document_processing_service.process_uploaded_document(document_id)
            )
            logger.info(f"Started background processing for document: {document_id}")
        except Exception as e:
            logger.warning(f"Failed to start background processing: {str(e)}")

        # Convert to response model
        document_response = DocumentResponse(**document_record)

        return UploadResponse(
            success=True,
            message=f"File '{file.filename}' uploaded successfully and processing started",
            document=document_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}"
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip")
):
    """
    List all uploaded documents with pagination.

    - **limit**: Maximum number of documents to return (1-100)
    - **offset**: Number of documents to skip for pagination

    Returns list of document metadata.
    """
    try:
        documents = await document_service.list_documents(limit=limit, offset=offset)

        # Convert to response models
        document_responses = [DocumentResponse(**doc) for doc in documents]

        return DocumentListResponse(
            documents=document_responses,
            total=len(document_responses),  # Note: This is the returned count, not total in DB
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str = Path(..., description="Document UUID")
):
    """
    Get document metadata by ID.

    - **document_id**: UUID of the document

    Returns document metadata.
    """
    try:
        document = await document_service.get_document(document_id)

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        return DocumentResponse(**document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document: {str(e)}"
        )


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str = Path(..., description="Document UUID"),
    expires_in: int = Query(3600, ge=300, le=86400, description="URL expiration time in seconds")
):
    """
    Get signed URL for document download.

    - **document_id**: UUID of the document
    - **expires_in**: URL expiration time in seconds (5 minutes to 24 hours)

    Redirects to signed URL for secure file access.
    """
    try:
        # Get document metadata
        document = await document_service.get_document(document_id)

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        # Generate signed URL
        signed_url = await storage_service.get_signed_url(
            document["storage_path"],
            expires_in=expires_in
        )

        # Redirect to signed URL
        return RedirectResponse(url=signed_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate download URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str = Path(..., description="Document UUID")
):
    """
    Delete document and associated files.

    - **document_id**: UUID of the document to delete

    Removes document from both storage and database.
    """
    try:
        # Get document metadata
        document = await document_service.get_document(document_id)

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        # Delete file from storage
        storage_deleted = await storage_service.delete_file(document["storage_path"])

        if not storage_deleted:
            logger.warning(f"Failed to delete file from storage: {document['storage_path']}")

        # Delete document record from database
        db_deleted = await document_service.delete_document(document_id)

        if not db_deleted:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete document record"
            )

        return DeleteResponse(
            success=True,
            message=f"Document '{document['original_name']}' deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_document_stats():
    """
    Get document statistics.

    Returns statistics about uploaded documents including counts and sizes.
    """
    try:
        stats = await document_service.get_document_stats()
        return DocumentStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get document stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document stats: {str(e)}"
        )


@router.post("/documents/{document_id}/process", response_model=ProcessingResponse)
async def process_document(
    document_id: str = Path(..., description="Document UUID")
):
    """
    Process uploaded document through PDF extraction and chunking pipeline.

    - **document_id**: UUID of the document to process

    Extracts text from PDF, creates chunks, and stores them in the database.
    """
    try:
        # Check if document exists
        document = await document_service.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        # Check if document is already processed
        if document["status"] == "ready":
            return ProcessingResponse(
                success=True,
                message="Document already processed",
                document_id=document_id
            )

        # Process the document
        success, error_message = await document_processing_service.process_uploaded_document(document_id)

        if success:
            return ProcessingResponse(
                success=True,
                message="Document processed successfully",
                document_id=document_id
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Document processing failed: {error_message}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get("/documents/{document_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    document_id: str = Path(..., description="Document UUID")
):
    """
    Get processing status for a document.

    - **document_id**: UUID of the document

    Returns processing status and chunk statistics.
    """
    try:
        status_info = await document_processing_service.get_processing_status(document_id)

        if "error" in status_info:
            raise HTTPException(
                status_code=404,
                detail=status_info["error"]
            )

        return ProcessingStatusResponse(**status_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get processing status: {str(e)}"
        )


@router.get("/documents/{document_id}/preview", response_model=DocumentPreviewResponse)
async def get_document_preview(
    document_id: str = Path(..., description="Document UUID"),
    max_chunks: int = Query(3, ge=1, le=10, description="Maximum number of chunks to preview")
):
    """
    Get a preview of document content.

    - **document_id**: UUID of the document
    - **max_chunks**: Maximum number of chunks to include in preview (1-10)

    Returns document preview with first few chunks.
    """
    try:
        preview = await document_processing_service.get_document_content_preview(
            document_id, max_chunks
        )

        if "error" in preview:
            raise HTTPException(
                status_code=404,
                detail=preview["error"]
            )

        return DocumentPreviewResponse(**preview)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document preview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document preview: {str(e)}"
        )


@router.post("/documents/{document_id}/reprocess", response_model=ProcessingResponse)
async def reprocess_document(
    document_id: str = Path(..., description="Document UUID")
):
    """
    Reprocess an existing document.

    - **document_id**: UUID of the document to reprocess

    Deletes existing chunks and reprocesses the document.
    """
    try:
        # Check if document exists
        document = await document_service.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        # Reprocess the document
        success, error_message = await document_processing_service.reprocess_document(document_id)

        if success:
            return ProcessingResponse(
                success=True,
                message="Document reprocessed successfully",
                document_id=document_id
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Document reprocessing failed: {error_message}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reprocess document: {str(e)}"
        )


@router.get("/health")
async def files_health_check():
    """
    Health check for file operations.

    Verifies storage and database connectivity.
    """
    try:
        # Test storage connectivity by listing files
        files = await storage_service.list_files(limit=1)
        storage_healthy = True

        # Test database connectivity
        stats = await document_service.get_document_stats()
        database_healthy = True

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "storage": {
                "healthy": storage_healthy,
                "bucket": "documents"
            },
            "database": {
                "healthy": database_healthy,
                "total_documents": stats.get("total_documents", 0)
            },
            "configuration": {
                "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
                "allowed_file_types": settings.ALLOWED_FILE_TYPES
            }
        }

    except Exception as e:
        logger.error(f"Files health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Files service unhealthy: {str(e)}"
        )