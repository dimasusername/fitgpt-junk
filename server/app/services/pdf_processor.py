"""
PDF processing service for text extraction and chunking.
"""
import logging
import re
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of text from a document."""
    content: str
    page_number: int
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]


@dataclass
class ProcessingResult:
    """Result of PDF processing operation."""
    success: bool
    chunks: List[DocumentChunk]
    total_pages: int
    total_chars: int
    error_message: Optional[str] = None


class PDFProcessor:
    """Service for processing PDF documents and extracting text."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        """
        Initialize PDF processor.
        
        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_pdf(self, file_content: bytes, filename: str) -> ProcessingResult:
        """
        Process PDF file and extract text chunks.
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename for metadata
            
        Returns:
            ProcessingResult with chunks or error information
        """
        try:
            # Extract text from PDF
            text_by_page = self._extract_text_from_pdf(file_content)
            
            if not text_by_page:
                return ProcessingResult(
                    success=False,
                    chunks=[],
                    total_pages=0,
                    total_chars=0,
                    error_message="No text content found in PDF"
                )
            
            # Create chunks from extracted text
            chunks = self._create_chunks(text_by_page, filename)
            
            total_chars = sum(len(page_text) for page_text in text_by_page.values())
            
            logger.info(f"Successfully processed PDF: {filename}, "
                       f"pages: {len(text_by_page)}, chunks: {len(chunks)}, "
                       f"total_chars: {total_chars}")
            
            return ProcessingResult(
                success=True,
                chunks=chunks,
                total_pages=len(text_by_page),
                total_chars=total_chars
            )
            
        except Exception as e:
            logger.error(f"Failed to process PDF {filename}: {str(e)}")
            return ProcessingResult(
                success=False,
                chunks=[],
                total_pages=0,
                total_chars=0,
                error_message=str(e)
            )

    def _extract_text_from_pdf(self, file_content: bytes) -> Dict[int, str]:
        """
        Extract text from PDF using pypdf.
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            Dictionary mapping page numbers to extracted text
            
        Raises:
            PdfReadError: If PDF is corrupted or unreadable
            Exception: For other processing errors
        """
        try:
            # Create PDF reader from bytes
            pdf_stream = BytesIO(file_content)
            reader = PdfReader(pdf_stream)
            
            # Check if PDF is encrypted
            if reader.is_encrypted:
                raise Exception("PDF is encrypted and cannot be processed")
            
            text_by_page = {}
            
            # Extract text from each page
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    # Extract text from page
                    text = page.extract_text()
                    
                    # Clean and normalize text
                    cleaned_text = self._clean_text(text)
                    
                    if cleaned_text.strip():  # Only add pages with content
                        text_by_page[page_num] = cleaned_text
                        
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {str(e)}")
                    continue
            
            return text_by_page
            
        except PdfReadError as e:
            raise Exception(f"PDF file is corrupted or unreadable: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to read PDF: {str(e)}")

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize excessive line breaks (3+ newlines become 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Normalize spaces (multiple spaces become single space)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text

    def _create_chunks(self, text_by_page: Dict[int, str], filename: str) -> List[DocumentChunk]:
        """
        Create text chunks from extracted text with overlap.
        
        Args:
            text_by_page: Dictionary mapping page numbers to text
            filename: Original filename for metadata
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        chunk_index = 0
        
        for page_num, page_text in text_by_page.items():
            if not page_text.strip():
                continue
                
            # Create chunks for this page
            page_chunks = self._chunk_text(
                page_text, 
                page_num, 
                chunk_index, 
                filename
            )
            
            chunks.extend(page_chunks)
            chunk_index += len(page_chunks)
        
        return chunks

    def _chunk_text(self, text: str, page_num: int, start_chunk_index: int, 
                   filename: str) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            page_num: Page number this text came from
            start_chunk_index: Starting index for chunk numbering
            filename: Original filename for metadata
            
        Returns:
            List of DocumentChunk objects
        """
        if len(text) <= self.chunk_size:
            # Text fits in one chunk
            return [DocumentChunk(
                content=text,
                page_number=page_num,
                chunk_index=start_chunk_index,
                start_char=0,
                end_char=len(text),
                metadata={
                    "filename": filename,
                    "page_number": page_num,
                    "chunk_size": len(text),
                    "is_complete_page": True
                }
            )]
        
        chunks = []
        chunk_index = start_chunk_index
        start_pos = 0
        
        while start_pos < len(text):
            # Calculate end position for this chunk
            end_pos = min(start_pos + self.chunk_size, len(text))
            
            # Try to break at word boundary if not at end of text
            if end_pos < len(text):
                # Look for last space within chunk
                last_space = text.rfind(' ', start_pos, end_pos)
                if last_space > start_pos:
                    end_pos = last_space
            
            # Extract chunk content
            chunk_content = text[start_pos:end_pos].strip()
            
            if chunk_content:  # Only add non-empty chunks
                chunks.append(DocumentChunk(
                    content=chunk_content,
                    page_number=page_num,
                    chunk_index=chunk_index,
                    start_char=start_pos,
                    end_char=end_pos,
                    metadata={
                        "filename": filename,
                        "page_number": page_num,
                        "chunk_size": len(chunk_content),
                        "is_complete_page": False,
                        "total_page_chars": len(text)
                    }
                ))
                chunk_index += 1
            
            # Move to next chunk with overlap
            if end_pos >= len(text):
                break
                
            # Calculate next start position with overlap
            next_start = end_pos - self.chunk_overlap
            
            # Ensure we make progress
            if next_start <= start_pos:
                next_start = start_pos + 1
                
            start_pos = next_start
        
        return chunks

    def validate_pdf(self, file_content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate PDF file without full processing.
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            pdf_stream = BytesIO(file_content)
            reader = PdfReader(pdf_stream)
            
            # Check if encrypted
            if reader.is_encrypted:
                return False, "PDF is encrypted and cannot be processed"
            
            # Check if has pages
            if len(reader.pages) == 0:
                return False, "PDF has no pages"
            
            # Try to extract text from first page
            try:
                first_page = reader.pages[0]
                text = first_page.extract_text()
                # Don't require text content - some PDFs might be image-only
                
            except Exception as e:
                return False, f"Cannot extract text from PDF: {str(e)}"
            
            return True, None
            
        except PdfReadError as e:
            return False, f"PDF file is corrupted: {str(e)}"
        except Exception as e:
            return False, f"Invalid PDF file: {str(e)}"

    def get_pdf_info(self, file_content: bytes) -> Dict[str, Any]:
        """
        Get basic information about PDF without full processing.
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            Dictionary with PDF information
        """
        try:
            pdf_stream = BytesIO(file_content)
            reader = PdfReader(pdf_stream)
            
            info = {
                "page_count": len(reader.pages),
                "is_encrypted": reader.is_encrypted,
                "metadata": {}
            }
            
            # Extract metadata if available
            if reader.metadata:
                metadata = {}
                for key, value in reader.metadata.items():
                    if isinstance(value, str):
                        metadata[key.replace('/', '')] = value
                info["metadata"] = metadata
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get PDF info: {str(e)}")
            return {
                "page_count": 0,
                "is_encrypted": False,
                "metadata": {},
                "error": str(e)
            }


# Global PDF processor instance with default settings
pdf_processor = PDFProcessor(chunk_size=1000, chunk_overlap=100)