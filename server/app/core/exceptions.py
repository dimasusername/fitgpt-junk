"""
Custom application exceptions.
"""
from typing import Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class ValidationError(AppException):
    """Validation error exception."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=400, detail=detail)


class NotFoundError(AppException):
    """Resource not found exception."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=404, detail=detail)


class DatabaseError(AppException):
    """Database operation error exception."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=500, detail=detail)


class ExternalAPIError(AppException):
    """External API error exception."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=502, detail=detail)


class StorageError(AppException):
    """Storage operation error exception."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=500, detail=detail)