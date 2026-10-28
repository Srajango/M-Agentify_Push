"""Bind validation and policy issuance — nodes: validate_bind_inputs,
bind_and_issue_policy."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from lead_domain.events import EventPublisher
from lead_domain.exceptions import ConflictError, NotFoundError, ValidationFailedError
from lead_domain.mappers import policy_to_dict
from lead_domain.models import LeadStatus, Policy, QuoteStatus
from lead_domain.process_graph import register_handler, run_transition
from lead_domain.repositories import LeadRepository, PolicyRepository, QuoteRepository
from lead_domain.services.decisions import maybe_expire_quote


def validate_bind_inputs(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: validate_bind_inputs (REQ-015). Effective date must be on or
    after today and on or before the quote's expiry date; the collected
    amount must equal the latest quote version's total. On success this
    chains straight to bind_and_issue_policy."""

    session = ctx["session"]
    publisher: EventPublisher = ctx["publisher"]
    lead_id: str = ctx["lead_id"]
    effective_date: date = ctx["effective_date"]
    collected_amount = ctx["collected_amount"]

    leads = LeadRepository(session)
    quotes = QuoteRepository(session)
    lead = leads.get(lead_id)
    if lead is None:
        raise NotFoundError(f"lead '{lead_id}' not found")
    quote = quotes.latest_for_lead(lead_id)

    if maybe_expire_quote(lead, quote, publisher):
        raise ConflictError("the quote has expired and the lead was automatically set to Lost")

    if quote is None or quote.status != QuoteStatus.ACTIVE or lead.status != LeadStatus.QUOTED:
        raise ConflictError("lead has no active quote to bind")

    today = datetime.utcnow().date()
    if effective_date < today or effective_date > quote.expires_at.date():
        raise ValidationFailedError(
            "effective_date must be on or after today and on or before the quote's expiry date"
        )
    if collected_amount != quote.total_premium:
        raise ValidationFailedError("collected_amount must equal the latest quote version's total")

    issue_context = {
        "session": session,
        "publisher": publisher,
        "lead_id": lead_id,
        "effective_date": effective_date,
    }
    return run_transition("validate_bind_inputs", "bind_and_issue_policy", issue_context)


def _generate_policy_number(policies: PolicyRepository, calendar_year: int) -> str:
    sequence = sum(1 for p in policies.list_all() if p.policy_number.startswith(f"PC-{calendar_year}-"))
    for attempt in range(sequence + 1, sequence + 1_000_000):
        candidate = f"PC-{calendar_year}-{attempt:06d}"
        if not policies.exists_with_number(candidate):
            return candidate
    raise RuntimeError("exhausted the six-digit policy number space for this calendar year")


def bind_and_issue_policy(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: bind_and_issue_policy (REQ-014). Issues a unique policy number
    PC-{calendar year}-{six digits}, stores the policy snapshot from the
    accepted quote version, and sets the lead to Converted."""

    session = ctx["session"]
    publisher: EventPublisher = ctx["publisher"]
    lead_id: str = ctx["lead_id"]
    effective_date: date = ctx["effective_date"]

    leads = LeadRepository(session)
    quotes = QuoteRepository(session)
    policies = PolicyRepository(session)

    lead = leads.get(lead_id)
    if lead is None:
        raise NotFoundError(f"lead '{lead_id}' not found")
    quote = quotes.latest_for_lead(lead_id)
    if quote is None or quote.status != QuoteStatus.ACTIVE:
        raise ConflictError("lead has no active quote to bind")

    calendar_year = datetime.utcnow().year
    policy_number = _generate_policy_number(policies, calendar_year)
    premium_breakdown = {
        "own_damage_premium": str(quote.own_damage_premium),
        "third_party_premium": str(quote.third_party_premium),
        "loading_amount": str(quote.loading_amount),
        "no_claim_bonus_amount": str(quote.no_claim_bonus_amount),
        "total_premium": str(quote.total_premium),
    }
    policy = Policy(
        lead_id=lead_id,
        quote_id=quote.quote_id,
        policy_number=policy_number,
        coverage_type=quote.coverage_type,
        idv=quote.idv,
        premium_breakdown=premium_breakdown,
        no_claim_bonus_amount=quote.no_claim_bonus_amount,
        loading_amount=quote.loading_amount,
        effective_date=effective_date,
    )
    policies.add(policy)
    quote.status = QuoteStatus.ACCEPTED

    previous_status = lead.status
    lead.status = LeadStatus.CONVERTED
    publisher.lead_status_changed(lead.lead_id, previous_status.value, lead.status.value)
    publisher.policy_issued(lead_id, policy.policy_id, policy.policy_number)

    return policy_to_dict(policy, lead.status.value)


register_handler("validate_bind_inputs", validate_bind_inputs)
register_handler("bind_and_issue_policy", bind_and_issue_policy)
