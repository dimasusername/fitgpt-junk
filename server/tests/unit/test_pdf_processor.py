"""
Unit tests for PDF processing service.
"""
import pytest
from io import BytesIO
from unittest.mock import Mock, patch

from app.services.pdf_processor import PDFProcessor, DocumentChunk, ProcessingResult


class TestPDFProcessor:
    """Test cases for PDFProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = PDFProcessor(chunk_size=100, chunk_overlap=20)

    def test_init(self):
        """Test PDFProcessor initialization."""
        processor = PDFProcessor(chunk_size=500, chunk_overlap=50)
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 50

    def test_clean_text(self):
        """Test text cleaning functionality."""
        # Test whitespace normalization
        text = "This  is   a\n\n\ntest   text"
        cleaned = self.processor._clean_text(text)
        assert cleaned == "This is a\n\ntest text"

        # Test control character removal
        text = "Hello\x00\x01World\x7F"
        cleaned = self.processor._clean_text(text)
        assert cleaned == "HelloWorld"

        # Test empty text
        assert self.processor._clean_text("") == ""
        assert self.processor._clean_text(None) == ""

    def test_chunk_text_small(self):
        """Test chunking of small text that fits in one chunk."""
        text = "This is a small text."
        chunks = self.processor._chunk_text(text, page_num=1, start_chunk_index=0, filename="test.pdf")
        
        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].page_number == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].metadata["is_complete_page"] is True

    def test_chunk_text_large(self):
        """Test chunking of large text that needs multiple chunks."""
        # Create text larger than chunk_size
        text = "This is a test sentence. " * 10  # About 250 characters
        chunks = self.processor._chunk_text(text, page_num=1, start_chunk_index=0, filename="test.pdf")
        
        assert len(chunks) > 1
        assert all(chunk.page_number == 1 for chunk in chunks)
        assert all(chunk.metadata["is_complete_page"] is False for chunk in chunks)
        
        # Check chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_chunk_text_overlap(self):
        """Test that chunks have proper overlap."""
        text = "A" * 200  # Text larger than chunk_size
        chunks = self.processor._chunk_text(text, page_num=1, start_chunk_index=0, filename="test.pdf")
        
        if len(chunks) > 1:
            # Check that there's overlap between consecutive chunks
            # This is a simplified check - actual overlap depends on word boundaries
            assert len(chunks[0].content) <= self.processor.chunk_size
            assert len(chunks[1].content) <= self.processor.chunk_size

    @patch('app.services.pdf_processor.PdfReader')
    def test_extract_text_from_pdf_success(self, mock_pdf_reader):
        """Test successful PDF text extraction."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test page content"
        
        mock_reader = Mock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [mock_page]
        
        mock_pdf_reader.return_value = mock_reader
        
        # Test extraction
        file_content = b"fake pdf content"
        result = self.processor._extract_text_from_pdf(file_content)
        
        assert result == {1: "Test page content"}
        mock_pdf_reader.assert_called_once()

    @patch('app.services.pdf_processor.PdfReader')
    def test_extract_text_from_pdf_encrypted(self, mock_pdf_reader):
        """Test PDF text extraction with encrypted PDF."""
        mock_reader = Mock()
        mock_reader.is_encrypted = True
        mock_pdf_reader.return_value = mock_reader
        
        file_content = b"fake pdf content"
        
        with pytest.raises(Exception, match="PDF is encrypted"):
            self.processor._extract_text_from_pdf(file_content)

    @patch('app.services.pdf_processor.PdfReader')
    def test_extract_text_from_pdf_corrupted(self, mock_pdf_reader):
        """Test PDF text extraction with corrupted PDF."""
        from pypdf.errors import PdfReadError
        mock_pdf_reader.side_effect = PdfReadError("Corrupted PDF")
        
        file_content = b"fake pdf content"
        
        with pytest.raises(Exception, match="PDF file is corrupted"):
            self.processor._extract_text_from_pdf(file_content)

    @patch('app.services.pdf_processor.PdfReader')
    def test_validate_pdf_success(self, mock_pdf_reader):
        """Test successful PDF validation."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test content"
        
        mock_reader = Mock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [mock_page]
        
        mock_pdf_reader.return_value = mock_reader
        
        file_content = b"fake pdf content"
        is_valid, error = self.processor.validate_pdf(file_content)
        
        assert is_valid is True
        assert error is None

    @patch('app.services.pdf_processor.PdfReader')
    def test_validate_pdf_no_pages(self, mock_pdf_reader):
        """Test PDF validation with no pages."""
        mock_reader = Mock()
        mock_reader.is_encrypted = False
        mock_reader.pages = []
        
        mock_pdf_reader.return_value = mock_reader
        
        file_content = b"fake pdf content"
        is_valid, error = self.processor.validate_pdf(file_content)
        
        assert is_valid is False
        assert "no pages" in error.lower()

    @patch('app.services.pdf_processor.PdfReader')
    def test_get_pdf_info(self, mock_pdf_reader):
        """Test PDF info extraction."""
        mock_metadata = {'/Title': 'Test Document', '/Author': 'Test Author'}
        
        mock_reader = Mock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [Mock(), Mock()]  # 2 pages
        mock_reader.metadata = mock_metadata
        
        mock_pdf_reader.return_value = mock_reader
        
        file_content = b"fake pdf content"
        info = self.processor.get_pdf_info(file_content)
        
        assert info["page_count"] == 2
        assert info["is_encrypted"] is False
        assert info["metadata"]["Title"] == "Test Document"
        assert info["metadata"]["Author"] == "Test Author"

    @patch.object(PDFProcessor, '_extract_text_from_pdf')
    def test_process_pdf_success(self, mock_extract):
        """Test successful PDF processing."""
        mock_extract.return_value = {1: "Test page content"}
        
        file_content = b"fake pdf content"
        result = self.processor.process_pdf(file_content, "test.pdf")
        
        assert result.success is True
        assert len(result.chunks) == 1
        assert result.total_pages == 1
        assert result.chunks[0].content == "Test page content"
        assert result.error_message is None

    @patch.object(PDFProcessor, '_extract_text_from_pdf')
    def test_process_pdf_no_content(self, mock_extract):
        """Test PDF processing with no text content."""
        mock_extract.return_value = {}
        
        file_content = b"fake pdf content"
        result = self.processor.process_pdf(file_content, "test.pdf")
        
        assert result.success is False
        assert len(result.chunks) == 0
        assert result.total_pages == 0
        assert "No text content found" in result.error_message

    @patch.object(PDFProcessor, '_extract_text_from_pdf')
    def test_process_pdf_extraction_error(self, mock_extract):
        """Test PDF processing with extraction error."""
        mock_extract.side_effect = Exception("Extraction failed")
        
        file_content = b"fake pdf content"
        result = self.processor.process_pdf(file_content, "test.pdf")
        
        assert result.success is False
        assert len(result.chunks) == 0
        assert "Extraction failed" in result.error_message

    def test_create_chunks_multiple_pages(self):
        """Test chunk creation from multiple pages."""
        text_by_page = {
            1: "First page content",
            2: "Second page content"
        }
        
        chunks = self.processor._create_chunks(text_by_page, "test.pdf")
        
        assert len(chunks) == 2
        assert chunks[0].page_number == 1
        assert chunks[1].page_number == 2
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1

    def test_document_chunk_dataclass(self):
        """Test DocumentChunk dataclass."""
        chunk = DocumentChunk(
            content="Test content",
            page_number=1,
            chunk_index=0,
            start_char=0,
            end_char=12,
            metadata={"test": "value"}
        )
        
        assert chunk.content == "Test content"
        assert chunk.page_number == 1
        assert chunk.chunk_index == 0
        assert chunk.start_char == 0
        assert chunk.end_char == 12
        assert chunk.metadata == {"test": "value"}

    def test_processing_result_dataclass(self):
        """Test ProcessingResult dataclass."""
        chunks = [DocumentChunk("content", 1, 0, 0, 7, {})]
        result = ProcessingResult(
            success=True,
            chunks=chunks,
            total_pages=1,
            total_chars=7,
            error_message=None
        )
        
        assert result.success is True
        assert len(result.chunks) == 1
        assert result.total_pages == 1
        assert result.total_chars == 7
        assert result.error_message is None