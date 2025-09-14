# Supabase Blob Storage Integration

This document describes the Supabase Storage integration implemented for the AI Chat Application.

## Overview

The storage integration provides secure file upload, download, and management capabilities using Supabase Storage as the backend. It includes:

- **File Upload**: Upload PDF files to Supabase Storage with validation
- **Secure Downloads**: Generate signed URLs for secure file access
- **File Management**: List, delete, and track file metadata
- **Database Integration**: Store file metadata in PostgreSQL with document tracking

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Supabase       │    │   PostgreSQL    │
│   Endpoints     │───▶│   Storage        │    │   Database      │
│                 │    │   (Blob Store)   │    │   (Metadata)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ StorageService  │    │ Bucket: documents│    │ documents table │
│ DocumentService │    │ Files: PDFs      │    │ document_chunks │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## API Endpoints

### File Upload
```http
POST /api/files/upload
Content-Type: multipart/form-data

file: [PDF file, max 25MB]
```

**Response:**
```json
{
  "success": true,
  "message": "File 'document.pdf' uploaded successfully",
  "document": {
    "id": "uuid",
    "filename": "20241212_123456_abc123_document.pdf",
    "original_name": "document.pdf",
    "storage_path": "documents/20241212_123456_abc123_document.pdf",
    "public_url": "https://...",
    "mime_type": "application/pdf",
    "size": 1024000,
    "uploaded_at": "2024-12-12T12:34:56Z",
    "status": "ready"
  }
}
```

### List Documents
```http
GET /api/files/documents?limit=50&offset=0
```

**Response:**
```json
{
  "documents": [...],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

### Get Document
```http
GET /api/files/documents/{document_id}
```

### Download Document
```http
GET /api/files/documents/{document_id}/download?expires_in=3600
```
*Redirects to signed URL for secure download*

### Delete Document
```http
DELETE /api/files/documents/{document_id}
```

### Document Statistics
```http
GET /api/files/stats
```

**Response:**
```json
{
  "total_documents": 5,
  "status_counts": {
    "processing": 1,
    "ready": 4,
    "error": 0
  },
  "total_size_bytes": 12500000,
  "total_size_mb": 11.92
}
```

### Health Check
```http
GET /api/files/health
```

## Services

### StorageService

Handles direct interaction with Supabase Storage:

- `upload_file(file)` - Upload file to storage bucket
- `get_signed_url(path, expires_in)` - Generate secure download URL
- `delete_file(path)` - Remove file from storage
- `list_files(prefix, limit)` - List files in bucket
- `get_file_info(path)` - Get file metadata

### DocumentService

Manages document metadata in PostgreSQL:

- `create_document(data)` - Create document record
- `get_document(id)` - Retrieve document by ID
- `list_documents(limit, offset)` - List documents with pagination
- `update_document_status(id, status)` - Update processing status
- `delete_document(id)` - Remove document and chunks
- `get_document_stats()` - Get document statistics

## Configuration

Required environment variables:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# File Configuration
MAX_FILE_SIZE=26214400  # 25MB
ALLOWED_FILE_TYPES=["application/pdf"]
```

## Storage Structure

Files are stored in Supabase Storage with the following structure:

```
documents/
├── 20241212_123456_abc123_document1.pdf
├── 20241212_134567_def456_document2.pdf
└── 20241212_145678_ghi789_document3.pdf
```

**Filename Format:** `YYYYMMDD_HHMMSS_uniqueid_originalname.ext`

## Database Schema

### documents table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,              -- Storage filename
    original_name TEXT NOT NULL,         -- User's original filename
    storage_path TEXT NOT NULL,          -- Full path in storage
    public_url TEXT,                     -- CDN URL
    mime_type TEXT NOT NULL,
    size INTEGER NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK (status IN ('processing', 'ready', 'error')),
    chunk_count INTEGER DEFAULT 0
);
```

### document_chunks table
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(768),               -- For RAG functionality
    page_number INTEGER,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Security Features

1. **File Validation**: Size limits, type checking, filename sanitization
2. **Signed URLs**: Temporary, secure access to files
3. **Private Storage**: Files not publicly accessible without signed URLs
4. **Input Sanitization**: Safe filename generation and path handling
5. **Error Handling**: Comprehensive error handling with user-friendly messages

## Error Handling

The integration includes comprehensive error handling:

- **Validation Errors**: File size, type, and format validation
- **Storage Errors**: Upload, download, and deletion failures
- **Database Errors**: Metadata operations and consistency
- **Network Errors**: Connection issues and timeouts
- **Authentication Errors**: Invalid credentials or permissions

## Usage Example

```python
from app.services.storage import storage_service
from app.services.documents import document_service

# Upload file
file_metadata = await storage_service.upload_file(upload_file)
document = await document_service.create_document(file_metadata)

# Get signed URL for download
signed_url = await storage_service.get_signed_url(
    document["storage_path"], 
    expires_in=3600
)

# Delete file and metadata
await storage_service.delete_file(document["storage_path"])
await document_service.delete_document(document["id"])
```

## Testing

Run the structure test to verify the integration:

```bash
cd server
python test_storage_structure.py
```

This validates that all components are properly implemented and configured.

## Next Steps

This storage integration is ready for:

1. **PDF Processing Pipeline** (Task 4) - Extract text from uploaded PDFs
2. **RAG Implementation** (Task 5) - Generate embeddings and store in document_chunks
3. **Frontend Integration** (Task 13) - Connect upload UI to these endpoints

The storage layer provides the foundation for the document-based RAG system that will be implemented in subsequent tasks.