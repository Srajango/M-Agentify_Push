"""Domain exceptions for lead-domain-service.

Raised by the service layer and translated to structured JSON HTTP responses
by the exception handlers registered in main.py.
"""

from __future__ import annotations


class LeadDomainServiceError(Exception):
    """Base exception for lead-domain-service."""

    status_code: int = 500
    error_code: str = "service_error"

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code:
            self.status_code = status_code


class NotFoundError(LeadDomainServiceError):
    """Resource (lead, risk, agent, quote, policy) not found."""

    status_code = 404
    error_code = "not_found"


class ValidationFailedError(LeadDomainServiceError):
    """Input passed schema validation but failed a business rule."""

    status_code = 422
    error_code = "validation_failed"


class DuplicateLeadError(LeadDomainServiceError):
    """A matching open lead already exists for this mobile + vehicle registration."""

    status_code = 409
    error_code = "duplicate_lead"


class ConflictError(LeadDomainServiceError):
    """The requested transition conflicts with the resource's current state."""

    status_code = 409
    error_code = "conflict"


class ForbiddenError(LeadDomainServiceError):
    """The caller's role does not permit this action."""

    status_code = 403
    error_code = "forbidden"
