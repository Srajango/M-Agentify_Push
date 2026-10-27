"""Quote rating — node: auto_rate_quote."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lead_domain.deps import publisher_dependency, session_dependency
from lead_domain.events import EventPublisher
from lead_domain.mappers import quote_to_dict
from lead_domain.process_graph import get_handler
from lead_domain.repositories import LeadRepository, QuoteRepository
from lead_domain.schemas import QuoteResponse

router = APIRouter(tags=["quotes"])


@router.post("/leads/{lead_id}/quote", response_model=QuoteResponse)
def rate_quote(
    lead_id: str,
    session: Session = Depends(session_dependency),
    publisher: EventPublisher = Depends(publisher_dependency),
) -> QuoteResponse:
    """Node: auto_rate_quote (REQ-009, REQ-010). Re-invoking on a Quoted
    lead re-rates it, storing a new higher version and replacing the prior
    one (REQ-012)."""

    result = get_handler("auto_rate_quote")(
        {"session": session, "publisher": publisher, "lead_id": lead_id}
    )
    return QuoteResponse.model_validate(result)


@router.get("/leads/{lead_id}/quotes", response_model=list[QuoteResponse])
def list_quotes(lead_id: str, session: Session = Depends(session_dependency)) -> list[QuoteResponse]:
    """REQ-012: lets a caller see every quote version, including replaced
    ones, to confirm only the newest can later be accepted."""

    lead = LeadRepository(session).get(lead_id)
    lead_status = lead.status.value if lead else ""
    quotes = QuoteRepository(session).list_for_lead(lead_id)
    return [QuoteResponse.model_validate(quote_to_dict(q, lead_status)) for q in quotes]
