from typing import Any


# ── Base ───────────────────────────────────────────────────────
class AppException(Exception):
    """Base exception for all application errors.
    
    Every custom exception inherits from this.
    Allows catching all app errors in one place with except AppException.
    """
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Any = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)


# ── Auth exceptions ────────────────────────────────────────────
class AuthenticationError(AppException):
    """Raised when credentials are invalid or missing."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED",
        )


class TokenExpiredError(AppException):
    """Raised when a JWT token has expired."""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="TOKEN_EXPIRED",
        )


class InsufficientPermissionsError(AppException):
    """Raised when a user lacks the required role."""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="INSUFFICIENT_PERMISSIONS",
        )


# ── Resource exceptions ────────────────────────────────────────
class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )


class AlreadyExistsError(AppException):
    """Raised when trying to create a resource that already exists."""
    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} with {field} '{value}' already exists",
            status_code=409,
            error_code="ALREADY_EXISTS",
            details={"resource": resource, "field": field, "value": str(value)},
        )


# ── Validation exceptions ──────────────────────────────────────
class ValidationError(AppException):
    """Raised when business logic validation fails.
    
    Different from Pydantic's ValidationError which handles
    request schema validation. This handles domain rules —
    e.g. 'document must be processed before chatting with it'.
    """
    def __init__(self, message: str, details: Any = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


# ── File exceptions ────────────────────────────────────────────
class FileTooLargeError(AppException):
    """Raised when an uploaded file exceeds the size limit."""
    def __init__(self, max_size_mb: int):
        super().__init__(
            message=f"File exceeds maximum allowed size of {max_size_mb}MB",
            status_code=413,
            error_code="FILE_TOO_LARGE",
            details={"max_size_mb": max_size_mb},
        )


class UnsupportedFileTypeError(AppException):
    """Raised when an uploaded file type is not allowed."""
    def __init__(self, file_type: str, allowed_types: list[str]):
        super().__init__(
            message=f"File type '{file_type}' is not supported",
            status_code=415,
            error_code="UNSUPPORTED_FILE_TYPE",
            details={"file_type": file_type, "allowed_types": allowed_types},
        )


# ── RAG exceptions ─────────────────────────────────────────────
class DocumentNotReadyError(AppException):
    """Raised when a user tries to chat with a document still processing."""
    def __init__(self, document_id: str):
        super().__init__(
            message="Document is still being processed, please wait",
            status_code=409,
            error_code="DOCUMENT_NOT_READY",
            details={"document_id": document_id},
        )


class RAGPipelineError(AppException):
    """Raised when the RAG pipeline fails during retrieval or generation."""
    def __init__(self, message: str = "RAG pipeline failed", details: Any = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="RAG_PIPELINE_ERROR",
            details=details,
        )


class ProviderNotConfiguredError(AppException):
    """Raised when a requested AI provider is not configured."""
    def __init__(self, provider_type: str, provider_name: str):
        super().__init__(
            message=f"Provider '{provider_name}' is not configured for {provider_type}",
            status_code=500,
            error_code="PROVIDER_NOT_CONFIGURED",
            details={"provider_type": provider_type, "provider_name": provider_name},
        )