"""Bind validation and policy issuance — nodes: validate_bind_inputs,
bind_and_issue_policy."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lead_domain.deps import publisher_dependency, session_dependency
from lead_domain.events import EventPublisher
from lead_domain.process_graph import get_handler
from lead_domain.schemas import BindRequest, BindResponse

router = APIRouter(tags=["bind"])


@router.post("/leads/{lead_id}/bind", response_model=BindResponse, status_code=201)
def bind_and_issue_policy(
    lead_id: str,
    payload: BindRequest,
    session: Session = Depends(session_dependency),
    publisher: EventPublisher = Depends(publisher_dependency),
) -> BindResponse:
    """Node: validate_bind_inputs (REQ-015), which on success chains
    straight into bind_and_issue_policy (REQ-014)."""

    result = get_handler("validate_bind_inputs")(
        {
            "session": session,
            "publisher": publisher,
            "lead_id": lead_id,
            "effective_date": payload.effective_date,
            "collected_amount": payload.collected_amount,
        }
    )
    return BindResponse.model_validate(result)
