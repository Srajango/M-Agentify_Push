"""Risk capture, appetite screening, underwriting outcome. Nodes:
capture_risk_data, auto_screen_appetite, record_underwriter_outcome."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lead_domain.deps import publisher_dependency, session_dependency
from lead_domain.events import EventPublisher
from lead_domain.process_graph import get_handler
from lead_domain.schemas import RiskResponse, RiskSubmitRequest, UnderwriterOutcomeRequest

router = APIRouter(tags=["risk"])


@router.post("/leads/{lead_id}/risk", response_model=RiskResponse)
def submit_risk_data(
    lead_id: str,
    payload: RiskSubmitRequest,
    session: Session = Depends(session_dependency),
    publisher: EventPublisher = Depends(publisher_dependency),
) -> RiskResponse:
    """Node: capture_risk_data (REQ-004)."""

    result = get_handler("capture_risk_data")(
        {"session": session, "publisher": publisher, "lead_id": lead_id, "payload": payload}
    )
    return RiskResponse.model_validate(result)


@router.post("/leads/{lead_id}/risk/screen", response_model=RiskResponse)
def screen_appetite(
    lead_id: str,
    session: Session = Depends(session_dependency),
    publisher: EventPublisher = Depends(publisher_dependency),
) -> RiskResponse:
    """Node: auto_screen_appetite (REQ-005, REQ-006)."""

    result = get_handler("auto_screen_appetite")(
        {"session": session, "publisher": publisher, "lead_id": lead_id}
    )
    return RiskResponse.model_validate(result)


@router.post("/leads/{lead_id}/risk/underwriting", response_model=RiskResponse)
def record_underwriter_outcome(
    lead_id: str,
    payload: UnderwriterOutcomeRequest,
    session: Session = Depends(session_dependency),
    publisher: EventPublisher = Depends(publisher_dependency),
) -> RiskResponse:
    """Node: record_underwriter_outcome (REQ-008); automatically chains to
    auto_rate_quote on approval."""

    result = get_handler("record_underwriter_outcome")(
        {
            "session": session,
            "publisher": publisher,
            "lead_id": lead_id,
            "outcome": payload.outcome,
            "loading_percent": payload.loading_percent,
        }
    )
    result.pop("quote", None)
    return RiskResponse.model_validate(result)
