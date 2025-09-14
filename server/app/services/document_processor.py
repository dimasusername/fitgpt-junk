"""
Document processing service that orchestrates PDF processing and storage.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from app.services.pdf_processor import pdf_processor, ProcessingResult
from app.services.documents import document_service
from app.services.chunks import chunk_service
from app.services.storage import storage_service
from app.services.embeddings import embedding_service

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Service for orchestrating document processing pipeline."""

    def __init__(self):
        self.pdf_processor = pdf_processor
        self.document_service = document_service
        self.chunk_service = chunk_service
        self.storage_service = storage_service
        self.embedding_service = embedding_service

    async def process_uploaded_document(self, document_id: str) -> Tuple[bool, Optional[str]]:
        """
        Process an uploaded document through the complete pipeline.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get document record
            document = await self.document_service.get_document(document_id)
            if not document:
                return False, "Document not found"
            
            # Update status to processing
            await self.document_service.update_document_status(document_id, "processing")
            
            # Download file from storage
            file_content = await self.storage_service.download_file(document["storage_path"])
            if not file_content:
                await self.document_service.update_document_status(document_id, "error")
                return False, "Failed to download file from storage"
            
            # Process PDF
            result = await self._process_pdf_content(
                file_content, 
                document["original_name"],
                document_id
            )
            
            if result[0]:  # Success
                chunk_count = len(result[2]) if len(result) > 2 else 0
                
                # Generate embeddings for the chunks
                if chunk_count > 0:
                    logger.info(f"Generating embeddings for {chunk_count} chunks in document {document_id}")
                    try:
                        await self._generate_document_embeddings(document_id)
                        logger.info(f"Successfully generated embeddings for document {document_id}")
                    except Exception as e:
                        logger.error(f"Failed to generate embeddings for document {document_id}: {str(e)}")
                        # Don't fail the entire process if embeddings fail
                        # The document is still usable for basic text search
                
                # Update document status to ready with chunk count
                await self.document_service.update_document_status(
                    document_id, "ready", chunk_count
                )
                logger.info(f"Document processing completed: {document_id}")
                return True, None
            else:
                # Update document status to error
                await self.document_service.update_document_status(document_id, "error")
                return False, result[1]
                
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {str(e)}")
            await self.document_service.update_document_status(document_id, "error")
            return False, str(e)

    async def _process_pdf_content(self, file_content: bytes, filename: str, 
                                 document_id: str) -> Tuple[bool, Optional[str], Optional[list]]:
        """
        Process PDF content and store chunks.
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            document_id: Document UUID
            
        Returns:
            Tuple of (success, error_message, chunks)
        """
        try:
            # Run PDF processing in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            processing_result: ProcessingResult = await loop.run_in_executor(
                None, self.pdf_processor.process_pdf, file_content, filename
            )
            
            if not processing_result.success:
                logger.error(f"PDF processing failed for {filename}: {processing_result.error_message}")
                return False, processing_result.error_message, None
            
            # Store chunks in database
            if processing_result.chunks:
                success = await self.chunk_service.store_chunks(document_id, processing_result.chunks)
                if not success:
                    return False, "Failed to store document chunks", None
            
            logger.info(f"Successfully processed PDF {filename}: "
                       f"{processing_result.total_pages} pages, "
                       f"{len(processing_result.chunks)} chunks, "
                       f"{processing_result.total_chars} characters")
            
            return True, None, processing_result.chunks
            
        except Exception as e:
            logger.error(f"Failed to process PDF content for {filename}: {str(e)}")
            return False, str(e), None

    async def validate_pdf_file(self, file_content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate PDF file before processing.
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Run validation in thread pool
            loop = asyncio.get_event_loop()
            is_valid, error_message = await loop.run_in_executor(
                None, self.pdf_processor.validate_pdf, file_content
            )
            
            return is_valid, error_message
            
        except Exception as e:
            logger.error(f"Failed to validate PDF: {str(e)}")
            return False, str(e)

    async def get_pdf_info(self, file_content: bytes) -> Dict[str, Any]:
        """
        Get PDF information without full processing.
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            Dictionary with PDF information
        """
        try:
            # Run info extraction in thread pool
            loop = asyncio.get_event_loop()
            pdf_info = await loop.run_in_executor(
                None, self.pdf_processor.get_pdf_info, file_content
            )
            
            return pdf_info
            
        except Exception as e:
            logger.error(f"Failed to get PDF info: {str(e)}")
            return {"error": str(e)}

    async def reprocess_document(self, document_id: str) -> Tuple[bool, Optional[str]]:
        """
        Reprocess an existing document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Delete existing chunks (this will also delete embeddings due to CASCADE)
            await self.chunk_service.delete_chunks_by_document(document_id)
            
            # Process document again (this will regenerate chunks and embeddings)
            return await self.process_uploaded_document(document_id)
            
        except Exception as e:
            logger.error(f"Failed to reprocess document {document_id}: {str(e)}")
            return False, str(e)

    async def get_processing_status(self, document_id: str) -> Dict[str, Any]:
        """
        Get processing status for a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Dictionary with processing status information
        """
        try:
            # Get document info
            document = await self.document_service.get_document(document_id)
            if not document:
                return {"error": "Document not found"}
            
            # Get chunk stats
            chunk_stats = await self.chunk_service.get_chunk_stats(document_id)
            
            return {
                "document_id": document_id,
                "status": document["status"],
                "filename": document["original_name"],
                "uploaded_at": document["uploaded_at"],
                "file_size": document["size"],
                "chunk_stats": chunk_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing status for {document_id}: {str(e)}")
            return {"error": str(e)}

    async def _generate_document_embeddings(self, document_id: str) -> bool:
        """
        Generate embeddings for all chunks of a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            True if embeddings generated successfully
        """
        try:
            # Get all chunks for the document
            chunks = await self.chunk_service.get_chunks_by_document(document_id)
            
            if not chunks:
                logger.warning(f"No chunks found for document {document_id}")
                return False
            
            # Extract text content from chunks
            texts = [chunk["content"] for chunk in chunks]
            
            # Generate embeddings in batches
            embedding_results = await self.embedding_service.generate_embeddings_batch(texts)
            
            if len(embedding_results) != len(chunks):
                logger.warning(f"Embedding count mismatch for document {document_id}: "
                             f"{len(embedding_results)} embeddings vs {len(chunks)} chunks")
            
            # Prepare chunk-embedding pairs for storage
            chunk_embeddings = []
            for i, embedding_result in enumerate(embedding_results):
                if i < len(chunks):
                    chunk_embeddings.append((chunks[i], embedding_result.embedding))
            
            # Store embeddings in database
            success = await self.embedding_service.store_embeddings(document_id, chunk_embeddings)
            
            if success:
                logger.info(f"Successfully generated and stored {len(chunk_embeddings)} embeddings for document {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings for document {document_id}: {str(e)}")
            return False

    async def regenerate_document_embeddings(self, document_id: str) -> Tuple[bool, Optional[str]]:
        """
        Regenerate embeddings for an existing document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Check if document exists and is ready
            document = await self.document_service.get_document(document_id)
            if not document:
                return False, "Document not found"
            
            if document["status"] != "ready":
                return False, f"Document status is {document['status']}, expected 'ready'"
            
            # Generate embeddings
            success = await self._generate_document_embeddings(document_id)
            
            if success:
                return True, None
            else:
                return False, "Failed to generate embeddings"
                
        except Exception as e:
            logger.error(f"Failed to regenerate embeddings for document {document_id}: {str(e)}")
            return False, str(e)

    async def get_document_content_preview(self, document_id: str, 
                                         max_chunks: int = 3) -> Dict[str, Any]:
        """
        Get a preview of document content.
        
        Args:
            document_id: Document UUID
            max_chunks: Maximum number of chunks to include in preview
            
        Returns:
            Dictionary with document preview
        """
        try:
            # Get document info
            document = await self.document_service.get_document(document_id)
            if not document:
                return {"error": "Document not found"}
            
            # Get first few chunks
            chunks = await self.chunk_service.get_chunks_by_document(document_id)
            preview_chunks = chunks[:max_chunks] if chunks else []
            
            # Create preview
            preview = {
                "document_id": document_id,
                "filename": document["original_name"],
                "status": document["status"],
                "total_chunks": len(chunks),
                "preview_chunks": [
                    {
                        "chunk_index": chunk["chunk_index"],
                        "page_number": chunk["page_number"],
                        "content_preview": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                        "content_length": len(chunk["content"])
                    }
                    for chunk in preview_chunks
                ]
            }
            
            return preview
            
        except Exception as e:
            logger.error(f"Failed to get document preview for {document_id}: {str(e)}")
            return {"error": str(e)}


# Global document processing service instance
document_processing_service = DocumentProcessingService()