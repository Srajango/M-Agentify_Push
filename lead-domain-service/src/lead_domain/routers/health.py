"""GET /health — frozen contract op_d05607ba2d958de5."""

from __future__ import annotations

from fastapi import APIRouter

from lead_domain.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
