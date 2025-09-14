"""
API tests for document processing endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestDocumentProcessingEndpoints:
    """Test cases for document processing API endpoints."""

    @patch('app.api.endpoints.files.document_service')
    @patch('app.api.endpoints.files.document_processing_service')
    def test_process_document_success(self, mock_processing_service, mock_document_service):
        """Test successful document processing endpoint."""
        # Mock document service
        mock_document = {
            "id": "test-doc-id",
            "status": "processing"
        }
        mock_document_service.get_document = AsyncMock(return_value=mock_document)
        
        # Mock processing service
        mock_processing_service.process_uploaded_document = AsyncMock(return_value=(True, None))
        
        response = client.post("/api/files/documents/test-doc-id/process")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["document_id"] == "test-doc-id"

    @patch('app.api.endpoints.files.document_service')
    def test_process_document_not_found(self, mock_document_service):
        """Test processing non-existent document."""
        mock_document_service.get_document = AsyncMock(return_value=None)
        
        response = client.post("/api/files/documents/nonexistent-id/process")
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]

    @patch('app.api.endpoints.files.document_service')
    @patch('app.api.endpoints.files.document_processing_service')
    def test_process_document_already_ready(self, mock_processing_service, mock_document_service):
        """Test processing document that's already ready."""
        # Mock document service
        mock_document = {
            "id": "test-doc-id",
            "status": "ready"
        }
        mock_document_service.get_document = AsyncMock(return_value=mock_document)
        
        response = client.post("/api/files/documents/test-doc-id/process")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "already processed" in data["message"]

    @patch('app.api.endpoints.files.document_processing_service')
    def test_get_processing_status_success(self, mock_processing_service):
        """Test getting processing status."""
        mock_status = {
            "document_id": "test-doc-id",
            "status": "ready",
            "filename": "test.pdf",
            "uploaded_at": "2023-01-01T00:00:00",
            "file_size": 1024,
            "chunk_stats": {"total_chunks": 5}
        }
        mock_processing_service.get_processing_status = AsyncMock(return_value=mock_status)
        
        response = client.get("/api/files/documents/test-doc-id/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-doc-id"
        assert data["status"] == "ready"

    @patch('app.api.endpoints.files.document_processing_service')
    def test_get_document_preview_success(self, mock_processing_service):
        """Test getting document preview."""
        mock_preview = {
            "document_id": "test-doc-id",
            "filename": "test.pdf",
            "status": "ready",
            "total_chunks": 2,
            "preview_chunks": [
                {
                    "chunk_index": 0,
                    "page_number": 1,
                    "content_preview": "Test content...",
                    "content_length": 100
                }
            ]
        }
        mock_processing_service.get_document_content_preview = AsyncMock(return_value=mock_preview)
        
        response = client.get("/api/files/documents/test-doc-id/preview")
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-doc-id"
        assert data["total_chunks"] == 2

    @patch('app.api.endpoints.files.document_service')
    @patch('app.api.endpoints.files.document_processing_service')
    def test_reprocess_document_success(self, mock_processing_service, mock_document_service):
        """Test document reprocessing."""
        # Mock document service
        mock_document = {
            "id": "test-doc-id",
            "status": "ready"
        }
        mock_document_service.get_document = AsyncMock(return_value=mock_document)
        
        # Mock processing service
        mock_processing_service.reprocess_document = AsyncMock(return_value=(True, None))
        
        response = client.post("/api/files/documents/test-doc-id/reprocess")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reprocessed successfully" in data["message"]

    @patch('app.api.endpoints.files.document_processing_service')
    def test_processing_status_not_found(self, mock_processing_service):
        """Test getting status for non-existent document."""
        mock_processing_service.get_processing_status = AsyncMock(
            return_value={"error": "Document not found"}
        )
        
        response = client.get("/api/files/documents/nonexistent-id/status")
        
        assert response.status_code == 404

    @patch('app.api.endpoints.files.document_processing_service')
    def test_document_preview_not_found(self, mock_processing_service):
        """Test getting preview for non-existent document."""
        mock_processing_service.get_document_content_preview = AsyncMock(
            return_value={"error": "Document not found"}
        )
        
        response = client.get("/api/files/documents/nonexistent-id/preview")
        
        assert response.status_code == 404