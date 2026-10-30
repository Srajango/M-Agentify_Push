"""Role-based lead listing and agency reporting counts — nodes:
role_based_access_control, compute_counts_conversion."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from lead_domain.deps import session_dependency
from lead_domain.process_graph import get_handler
from lead_domain.schemas import CountsResponse, LeadListResponse

router = APIRouter(tags=["reporting"])


@router.get("/leads", response_model=LeadListResponse)
def list_leads(
    role: str = Query(...),
    agent_id: Optional[str] = Query(default=None),
    session: Session = Depends(session_dependency),
) -> LeadListResponse:
    """Node: role_based_access_control (REQ-017)."""

    result = get_handler("role_based_access_control")(
        {"session": session, "role": role, "agent_id": agent_id}
    )
    return LeadListResponse.model_validate(result)


@router.get("/counts", response_model=CountsResponse)
def counts(session: Session = Depends(session_dependency)) -> CountsResponse:
    """Node: compute_counts_conversion (REQ-018)."""

    result = get_handler("compute_counts_conversion")({"session": session})
    return CountsResponse.model_validate(result)
