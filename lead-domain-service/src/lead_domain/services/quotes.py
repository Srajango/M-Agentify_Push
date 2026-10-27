"""Rate card engine and versioned quoting — node: auto_rate_quote."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any

from lead_domain.config import get_settings
from lead_domain.events import EventPublisher
from lead_domain.exceptions import ConflictError, NotFoundError, ValidationFailedError
from lead_domain.mappers import quote_to_dict
from lead_domain.models import Lead, LeadStatus, Quote, QuoteStatus
from lead_domain.process_graph import register_handler
from lead_domain.rate_card import rate_risk
from lead_domain.repositories import LeadRepository, QuoteRepository, RiskRepository


def _require_lead(leads: LeadRepository, lead_id: str) -> Lead:
    lead = leads.get(lead_id)
    if lead is None:
        raise NotFoundError(f"lead '{lead_id}' not found")
    return lead


def _end_of_day(day_date) -> datetime:
    return datetime.combine(day_date, time(23, 59, 59))


def auto_rate_quote(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: auto_rate_quote (REQ-009, REQ-010, REQ-012). Reads the latest
    approved risk, applies the agency rate card, stores a new quote version
    with a seven-day expiry, marks any prior version Replaced, and sets the
    lead to Quoted. Re-invoking on an already-Quoted lead re-rates it."""

    session = ctx["session"]
    publisher: EventPublisher = ctx["publisher"]
    lead_id: str = ctx["lead_id"]
    settings = ctx.get("settings") or get_settings()

    leads = LeadRepository(session)
    risks = RiskRepository(session)
    quotes = QuoteRepository(session)

    lead = _require_lead(leads, lead_id)
    if lead.status not in (LeadStatus.APPROVED, LeadStatus.QUOTED):
        raise ConflictError("lead must have an approved risk before it can be rated")

    risk = risks.latest_approved_for_lead(lead_id)
    if risk is None:
        raise ValidationFailedError("no approved risk is available to rate")
    if risk.coverage_type is None or risk.idv is None:
        raise ValidationFailedError("the approved risk is missing coverage_type or idv")

    pricing = rate_risk(
        coverage_type=risk.coverage_type,
        idv=risk.idv,
        no_claim_bonus_fraction=risk.no_claim_bonus_fraction or Decimal("0"),
        loading_percent=risk.loading_percent or Decimal("0"),
        third_party_base_premium=settings.rate_card_third_party_base_premium,
        own_damage_rate=settings.rate_card_own_damage_rate,
    )

    existing_quotes = quotes.list_for_lead(lead_id)
    for existing in existing_quotes:
        if existing.status == QuoteStatus.ACTIVE:
            existing.status = QuoteStatus.REPLACED

    rated_at = datetime.utcnow()
    expires_at = _end_of_day((rated_at + timedelta(days=7)).date())

    quote = Quote(
        lead_id=lead_id,
        risk_id=risk.risk_id,
        version=len(existing_quotes) + 1,
        coverage_type=risk.coverage_type,
        idv=risk.idv,
        own_damage_premium=pricing["own_damage_premium"],
        third_party_premium=pricing["third_party_premium"],
        no_claim_bonus_amount=pricing["no_claim_bonus_amount"],
        loading_amount=pricing["loading_amount"],
        total_premium=pricing["total_premium"],
        status=QuoteStatus.ACTIVE,
        rated_at=rated_at,
        expires_at=expires_at,
    )
    quotes.add(quote)

    previous_status = lead.status
    lead.status = LeadStatus.QUOTED
    if previous_status != lead.status:
        publisher.lead_status_changed(lead.lead_id, previous_status.value, lead.status.value)
    publisher.quote_issued(lead_id, quote.quote_id, quote.version, str(quote.total_premium))

    return quote_to_dict(quote, lead.status.value)


register_handler("auto_rate_quote", auto_rate_quote)
