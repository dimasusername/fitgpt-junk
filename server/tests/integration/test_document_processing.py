"""
Integration tests for document processing pipeline.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.services.pdf_processor import ProcessingResult, DocumentChunk


class TestDocumentProcessingIntegration:
    """Integration test cases for document processing pipeline."""

    @pytest.mark.asyncio
    @patch('app.services.document_processor.document_service')
    @patch('app.services.document_processor.storage_service') 
    @patch('app.services.document_processor.chunk_service')
    async def test_full_document_processing_pipeline(self, mock_chunk_service, 
                                                   mock_storage_service, mock_document_service):
        """Test the complete document processing pipeline."""
        from app.services.document_processor import document_processing_service
        
        # Mock document service
        mock_document = {
            "id": "test-doc-id",
            "original_name": "test.pdf",
            "storage_path": "documents/test.pdf"
        }
        mock_document_service.get_document = AsyncMock(return_value=mock_document)
        mock_document_service.update_document_status = AsyncMock(return_value=True)

        # Mock storage service
        mock_storage_service.download_file = AsyncMock(return_value=b"fake pdf content")

        # Mock chunk service
        mock_chunk_service.store_chunks = AsyncMock(return_value=True)

        # Mock PDF processing
        mock_chunks = [
            DocumentChunk("Test content", 1, 0, 0, 12, {"filename": "test.pdf"})
        ]
        
        with patch.object(document_processing_service.pdf_processor, 'process_pdf') as mock_process_pdf:
            mock_result = ProcessingResult(True, mock_chunks, 1, 12)
            mock_process_pdf.return_value = mock_result
            
            success, error = await document_processing_service.process_uploaded_document("test-doc-id")
            
            assert success is True
            assert error is None
            
            # Verify the pipeline was executed
            mock_document_service.get_document.assert_called_once_with("test-doc-id")
            mock_document_service.update_document_status.assert_any_call("test-doc-id", "processing")
            mock_document_service.update_document_status.assert_any_call("test-doc-id", "ready", 1)
            mock_storage_service.download_file.assert_called_once_with("documents/test.pdf")
            mock_chunk_service.store_chunks.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.document_processor.document_service')
    async def test_document_not_found(self, mock_document_service):
        """Test processing with document not found."""
        from app.services.document_processor import document_processing_service
        
        mock_document_service.get_document = AsyncMock(return_value=None)
        
        success, error = await document_processing_service.process_uploaded_document("nonexistent-id")
        
        assert success is False
        assert error == "Document not found"

    @pytest.mark.asyncio
    @patch('app.services.document_processor.document_service')
    @patch('app.services.document_processor.storage_service')
    async def test_storage_download_failure(self, mock_storage_service, mock_document_service):
        """Test processing with storage download failure."""
        from app.services.document_processor import document_processing_service
        
        mock_document = {"id": "test-doc-id", "storage_path": "documents/test.pdf"}
        mock_document_service.get_document = AsyncMock(return_value=mock_document)
        mock_document_service.update_document_status = AsyncMock(return_value=True)
        mock_storage_service.download_file = AsyncMock(return_value=None)
        
        success, error = await document_processing_service.process_uploaded_document("test-doc-id")
        
        assert success is False
        assert "Failed to download file" in error
        mock_document_service.update_document_status.assert_any_call("test-doc-id", "error")

    @pytest.mark.asyncio
    @patch('app.services.document_processor.document_service')
    @patch('app.services.document_processor.chunk_service')
    async def test_pdf_processing_failure(self, mock_chunk_service, mock_document_service):
        """Test processing with PDF processing failure."""
        from app.services.document_processor import document_processing_service
        
        mock_document = {
            "id": "test-doc-id",
            "original_name": "test.pdf",
            "storage_path": "documents/test.pdf"
        }
        mock_document_service.get_document = AsyncMock(return_value=mock_document)
        mock_document_service.update_document_status = AsyncMock(return_value=True)

        # Mock failed PDF processing
        with patch.object(document_processing_service.pdf_processor, 'process_pdf') as mock_process_pdf:
            mock_result = ProcessingResult(False, [], 0, 0, "PDF processing failed")
            mock_process_pdf.return_value = mock_result
            
            with patch.object(document_processing_service.storage_service, 'download_file', 
                            return_value=AsyncMock(return_value=b"fake pdf content")()):
                
                success, error = await document_processing_service.process_uploaded_document("test-doc-id")
                
                assert success is False
                assert "PDF processing failed" in error
                mock_document_service.update_document_status.assert_any_call("test-doc-id", "error")

    @pytest.mark.asyncio
    async def test_pdf_validation(self):
        """Test PDF validation functionality."""
        from app.services.document_processor import document_processing_service
        
        file_content = b"fake pdf content"
        
        with patch.object(document_processing_service.pdf_processor, 'validate_pdf', 
                         return_value=(True, None)) as mock_validate:
            
            is_valid, error = await document_processing_service.validate_pdf_file(file_content)
            
            assert is_valid is True
            assert error is None
            mock_validate.assert_called_once_with(file_content)

    @pytest.mark.asyncio
    async def test_pdf_info_extraction(self):
        """Test PDF info extraction."""
        from app.services.document_processor import document_processing_service
        
        file_content = b"fake pdf content"
        expected_info = {"page_count": 2, "is_encrypted": False}
        
        with patch.object(document_processing_service.pdf_processor, 'get_pdf_info', 
                         return_value=expected_info) as mock_info:
            
            info = await document_processing_service.get_pdf_info(file_content)
            
            assert info == expected_info
            mock_info.assert_called_once_with(file_content)