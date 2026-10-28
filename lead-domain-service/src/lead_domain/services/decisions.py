"""Client quote decision and the automatic quote-expiry check — node:
client_decision_wait."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from lead_domain.events import EventPublisher
from lead_domain.exceptions import ConflictError, NotFoundError, ValidationFailedError
from lead_domain.models import Lead, LeadStatus, Quote, QuoteStatus
from lead_domain.process_graph import register_handler
from lead_domain.repositories import LeadRepository, QuoteRepository

QUOTE_EXPIRED_REASON = "Quote expired"


def maybe_expire_quote(lead: Lead, quote: Quote | None, publisher: EventPublisher) -> bool:
    """REQ-013's automatic check: once the seventh day ends with no
    acceptance, the lead is set to Lost with reason 'Quote expired' without
    any human choosing it. Returns True if this call performed the
    expiry transition."""

    if quote is None or quote.status != QuoteStatus.ACTIVE:
        return False
    if lead.status != LeadStatus.QUOTED:
        return False
    if datetime.utcnow() <= quote.expires_at:
        return False

    previous_status = lead.status
    quote.status = QuoteStatus.EXPIRED
    lead.status = LeadStatus.LOST
    lead.lost_reason = QUOTE_EXPIRED_REASON
    publisher.lead_status_changed(
        lead.lead_id, previous_status.value, lead.status.value, QUOTE_EXPIRED_REASON
    )
    return True


def client_decision_wait(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: client_decision_wait (REQ-013). Decline records a reason and
    sets the lead Lost; accept reports the current quote status so the case
    can proceed to bind. Applies the automatic quote-expiry check first."""

    session = ctx["session"]
    publisher: EventPublisher = ctx["publisher"]
    lead_id: str = ctx["lead_id"]
    action: str = ctx["action"]
    reason: str | None = ctx.get("reason")

    leads = LeadRepository(session)
    quotes = QuoteRepository(session)
    lead = leads.get(lead_id)
    if lead is None:
        raise NotFoundError(f"lead '{lead_id}' not found")
    quote = quotes.latest_for_lead(lead_id)

    if maybe_expire_quote(lead, quote, publisher):
        raise ConflictError("the quote has expired and the lead was automatically set to Lost")

    if quote is None or quote.status != QuoteStatus.ACTIVE or lead.status != LeadStatus.QUOTED:
        raise ConflictError("lead has no active quote awaiting a client decision")

    if action == "decline":
        if reason is None:
            raise ValidationFailedError("reason is required to decline a quote")
        previous_status = lead.status
        quote.status = QuoteStatus.DECLINED
        lead.status = LeadStatus.LOST
        lead.lost_reason = reason
        publisher.lead_status_changed(lead.lead_id, previous_status.value, lead.status.value, reason)
        return {
            "lead_id": lead.lead_id,
            "lead_status": lead.status.value,
            "lost_reason": lead.lost_reason,
            "quote_id": quote.quote_id,
            "quote_status": quote.status.value,
            "total_premium": quote.total_premium,
            "expires_at": quote.expires_at,
        }

    return {
        "lead_id": lead.lead_id,
        "lead_status": lead.status.value,
        "lost_reason": None,
        "quote_id": quote.quote_id,
        "quote_status": quote.status.value,
        "total_premium": quote.total_premium,
        "expires_at": quote.expires_at,
    }


register_handler("client_decision_wait", client_decision_wait)
