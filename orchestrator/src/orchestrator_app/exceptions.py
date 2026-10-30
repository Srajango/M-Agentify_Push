"""Domain exceptions for the orchestrator service.

Raised by business logic (graph nodes, the domain client, routers) and caught
at the HTTP boundary to produce the right status code. Never a bare
except/raise in handler code — always one of these.
"""

from __future__ import annotations


class OrchestratorError(Exception):
    """Base exception for every domain error raised by this service."""

    status_code: int = 500
    error_type: str = "service_error"

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class RunNotFoundError(OrchestratorError):
    """No run exists for the given run id."""

    status_code = 404
    error_type = "run_not_found"


class ValidationError(OrchestratorError):
    """Request or business input failed validation."""

    status_code = 422
    error_type = "validation_error"


class GateNotAwaitingApprovalError(OrchestratorError):
    """A resume/reject call targeted a gate the run is not paused at."""

    status_code = 409
    error_type = "gate_not_awaiting_approval"


class DomainServiceError(OrchestratorError):
    """The lead-domain-service dependency failed after exhausting retries."""

    status_code = 502
    error_type = "domain_service_error"
