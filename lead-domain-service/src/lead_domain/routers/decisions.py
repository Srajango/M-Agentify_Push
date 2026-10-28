"""Client quote decision — node: client_decision_wait."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lead_domain.deps import publisher_dependency, session_dependency
from lead_domain.events import EventPublisher
from lead_domain.process_graph import get_handler
from lead_domain.schemas import ClientDecisionRequest, ClientDecisionResponse

router = APIRouter(tags=["decisions"])


@router.post("/leads/{lead_id}/decision", response_model=ClientDecisionResponse)
def client_decision(
    lead_id: str,
    payload: ClientDecisionRequest,
    session: Session = Depends(session_dependency),
    publisher: EventPublisher = Depends(publisher_dependency),
) -> ClientDecisionResponse:
    """Node: client_decision_wait (REQ-013). Applies the automatic
    'Quote expired' check before processing an accept or decline."""

    result = get_handler("client_decision_wait")(
        {
            "session": session,
            "publisher": publisher,
            "lead_id": lead_id,
            "action": payload.action,
            "reason": payload.reason,
        }
    )
    return ClientDecisionResponse.model_validate(result)
