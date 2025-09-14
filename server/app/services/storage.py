"""
Supabase Storage service for file operations.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import mimetypes

from fastapi import UploadFile, HTTPException
from supabase import Client

from app.core.database import get_supabase
from app.core.config import settings
from app.core.exceptions import StorageError

logger = logging.getLogger(__name__)

# Storage bucket name for documents
DOCUMENTS_BUCKET = "documents"


class StorageService:
    """Service for handling file storage operations with Supabase Storage."""

    def __init__(self):
        self.client: Optional[Client] = None

    def _get_client(self) -> Client:
        """Get Supabase client."""
        if self.client is None:
            self.client = get_supabase()
        return self.client

    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        # Check file size
        if hasattr(file, 'size') and file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )

        # Check file type
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )

        # Check filename
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )

    def _generate_storage_path(self, original_filename: str) -> str:
        """Generate unique storage path for file."""
        # Generate unique filename with timestamp and UUID
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = Path(original_filename).suffix

        # Create storage path: documents/YYYYMMDD_HHMMSS_uniqueid_filename.ext
        safe_filename = Path(original_filename).stem.replace(" ", "_")[:50]  # Limit length
        storage_filename = f"{timestamp}_{unique_id}_{safe_filename}{file_extension}"

        return f"documents/{storage_filename}"

    async def upload_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Upload file to Supabase Storage.

        Args:
            file: FastAPI UploadFile object

        Returns:
            Dict containing file metadata and storage information

        Raises:
            HTTPException: If upload fails or validation fails
        """
        try:
            # Validate file
            self._validate_file(file)

            # Read file content
            file_content = await file.read()
            actual_size = len(file_content)

            # Additional size check after reading
            if actual_size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
                )

            # Generate storage path
            storage_path = self._generate_storage_path(file.filename)

            # Upload to Supabase Storage
            client = self._get_client()

            # Ensure bucket exists (create if not exists)
            try:
                client.storage.get_bucket(DOCUMENTS_BUCKET)
            except Exception:
                # Bucket doesn't exist, create it
                client.storage.create_bucket(DOCUMENTS_BUCKET, options={"public": False})
                logger.info(f"Created storage bucket: {DOCUMENTS_BUCKET}")

            # Upload file
            result = client.storage.from_(DOCUMENTS_BUCKET).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": file.content_type,
                    "cache-control": "3600"
                }
            )

            if hasattr(result, 'error') and result.error:
                raise StorageError(f"Upload failed: {result.error}")

            # Get public URL (for signed URLs later)
            public_url_result = client.storage.from_(DOCUMENTS_BUCKET).get_public_url(storage_path)
            public_url = public_url_result if isinstance(public_url_result, str) else None

            # Prepare file metadata
            file_metadata = {
                "id": str(uuid.uuid4()),
                "filename": storage_path.split('/')[-1],  # Storage filename
                "original_name": file.filename,
                "storage_path": storage_path,
                "public_url": public_url,
                "mime_type": file.content_type,
                "size": actual_size,
                "uploaded_at": datetime.utcnow(),
                "status": "ready"
            }

            logger.info(f"File uploaded successfully: {file.filename} -> {storage_path}")
            return file_metadata

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {str(e)}"
            )
        finally:
            # Reset file position for potential reuse
            if hasattr(file, 'seek'):
                await file.seek(0)

    async def download_file(self, storage_path: str) -> Optional[bytes]:
        """
        Download file content from Supabase Storage.
        
        Args:
            storage_path: Path to file in storage
            
        Returns:
            File content as bytes or None if not found
            
        Raises:
            HTTPException: If download fails
        """
        try:
            client = self._get_client()
            
            # Download file from storage
            response = client.storage.from_(DOCUMENTS_BUCKET).download(storage_path)
            
            if response:
                logger.info(f"Downloaded file: {storage_path}")
                return response
            else:
                logger.warning(f"File not found in storage: {storage_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to download file {storage_path}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download file: {str(e)}"
            )

    async def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        Get signed URL for secure file access.

        Args:
            storage_path: Path to file in storage
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Signed URL for file access

        Raises:
            HTTPException: If URL generation fails
        """
        try:
            client = self._get_client()

            # Generate signed URL
            result = client.storage.from_(DOCUMENTS_BUCKET).create_signed_url(
                path=storage_path,
                expires_in=expires_in
            )

            if hasattr(result, 'error') and result.error:
                raise StorageError(f"Signed URL generation failed: {result.error}")

            # Extract URL from result
            signed_url = result.get('signedURL') if isinstance(result, dict) else result

            if not signed_url:
                raise StorageError("Failed to generate signed URL")

            logger.info(f"Generated signed URL for: {storage_path}")
            return signed_url

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Signed URL generation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate download URL: {str(e)}"
            )

    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete file from Supabase Storage.

        Args:
            storage_path: Path to file in storage

        Returns:
            True if deletion successful

        Raises:
            HTTPException: If deletion fails
        """
        try:
            client = self._get_client()

            # Delete file from storage
            result = client.storage.from_(DOCUMENTS_BUCKET).remove([storage_path])

            if hasattr(result, 'error') and result.error:
                raise StorageError(f"File deletion failed: {result.error}")

            logger.info(f"File deleted successfully: {storage_path}")
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File deletion failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"File deletion failed: {str(e)}"
            )

    async def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """
        List files in storage bucket.

        Args:
            prefix: Filter files by path prefix
            limit: Maximum number of files to return

        Returns:
            List of file metadata dictionaries
        """
        try:
            client = self._get_client()

            # List files in bucket
            result = client.storage.from_(DOCUMENTS_BUCKET).list(
                path=prefix,
                limit=limit,
                offset=0
            )

            if hasattr(result, 'error') and result.error:
                raise StorageError(f"File listing failed: {result.error}")

            # Format file information
            files = []
            for file_info in result:
                if isinstance(file_info, dict):
                    files.append({
                        "name": file_info.get("name"),
                        "size": file_info.get("metadata", {}).get("size", 0),
                        "last_modified": file_info.get("updated_at"),
                        "content_type": file_info.get("metadata", {}).get("mimetype"),
                        "storage_path": f"{prefix}/{file_info.get('name')}" if prefix else file_info.get("name")
                    })

            return files

        except Exception as e:
            logger.error(f"File listing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list files: {str(e)}"
            )

    async def get_file_info(self, storage_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from storage.

        Args:
            storage_path: Path to file in storage

        Returns:
            File metadata dictionary or None if not found
        """
        try:
            # Extract directory and filename from storage path
            path_parts = storage_path.split('/')
            if len(path_parts) > 1:
                directory = '/'.join(path_parts[:-1])
                filename = path_parts[-1]
            else:
                directory = ""
                filename = storage_path

            # List files in directory
            files = await self.list_files(prefix=directory)

            # Find specific file
            for file_info in files:
                if file_info["name"] == filename:
                    return file_info

            return None

        except Exception as e:
            logger.error(f"Failed to get file info: {str(e)}")
            return None


# Global storage service instance
storage_service = StorageService()