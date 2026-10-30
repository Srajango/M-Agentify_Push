"""Exception and error handling for approval-ui.

Domain-specific exceptions used throughout the service. These are raised in
business logic and caught by HTTP handlers for appropriate status codes.
"""

from __future__ import annotations


class ApprovalUiError(Exception):
    """Base exception for approval-ui."""

    status_code: int = 500
    error_type: str = "service_error"

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code:
            self.status_code = status_code


class NotFoundError(ApprovalUiError):
    """Resource not found."""
    status_code = 404


class ValidationError(ApprovalUiError):
    """Input validation failed."""
    status_code = 422


class ConflictError(ApprovalUiError):
    """Resource already exists or conflict detected."""
    status_code = 409


class UnauthorizedError(ApprovalUiError):
    """User not authenticated or permission denied."""
    status_code = 403


class ExternalServiceError(ApprovalUiError):
    """Dependency (database, external API) failed."""
    status_code = 502


# Add service-specific exceptions below
# class <Condition>Error(ApprovalUiError):
#     """<What must hold before this operation can proceed>."""
#     status_code = 409
