"""Risk capture, appetite screening and underwriting outcome — nodes:
capture_risk_data, auto_screen_appetite, record_underwriter_outcome."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from lead_domain.events import EventPublisher
from lead_domain.exceptions import ConflictError, NotFoundError, ValidationFailedError
from lead_domain.mappers import risk_to_dict
from lead_domain.models import AppetiteOutcome, CoverageType, Lead, LeadStatus, Risk, UnderwriterOutcome
from lead_domain.process_graph import register_handler, run_transition
from lead_domain.repositories import LeadRepository, RiskRepository
from lead_domain.schemas import RiskSubmitRequest

REQUIRED_RISK_FIELDS: tuple[str, ...] = (
    "vehicle_make",
    "vehicle_model",
    "registration_year",
    "idv",
    "coverage_type",
    "no_claim_bonus_fraction",
    "prior_claims_count",
)


def _missing_fields(risk: Risk) -> list[str]:
    return [field for field in REQUIRED_RISK_FIELDS if getattr(risk, field) is None]


def _require_lead(leads: LeadRepository, lead_id: str) -> Lead:
    lead = leads.get(lead_id)
    if lead is None:
        raise NotFoundError(f"lead '{lead_id}' not found")
    return lead


def capture_risk_data(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: capture_risk_data (REQ-004). Keeps status at Capture, and the
    case does not proceed, until every required fact is present."""

    session = ctx["session"]
    publisher: EventPublisher = ctx["publisher"]
    lead_id: str = ctx["lead_id"]
    payload: RiskSubmitRequest = ctx["payload"]

    leads = LeadRepository(session)
    risks = RiskRepository(session)
    lead = _require_lead(leads, lead_id)
    if lead.status in (LeadStatus.LOST, LeadStatus.CONVERTED):
        raise ConflictError(f"a {lead.status.value} lead cannot capture risk data")

    risk = risks.latest_for_lead(lead_id)
    if risk is None:
        risk = Risk(lead_id=lead_id)
        risks.add(risk)
    elif risk.appetite_outcome is not None:
        raise ConflictError("this lead's risk has already been screened; capture is closed")

    for field in REQUIRED_RISK_FIELDS:
        value = getattr(payload, field)
        if value is not None:
            if field == "coverage_type":
                value = CoverageType(value)
            setattr(risk, field, value)

    missing = _missing_fields(risk)
    risk.is_complete = not missing

    previous_status = lead.status
    if lead.status == LeadStatus.NEW:
        lead.status = LeadStatus.CAPTURE
    if previous_status != lead.status:
        publisher.lead_status_changed(lead.lead_id, previous_status.value, lead.status.value)

    return risk_to_dict(risk, lead.status.value, missing)


def _evaluate_decline_rules(risk: Risk) -> str | None:
    """Ordered decline rules, first match wins."""

    current_year = datetime.now(timezone.utc).year
    if risk.registration_year is not None and (current_year - risk.registration_year) > 15:
        return "Vehicle is older than 15 years"
    if risk.idv is not None and risk.idv < Decimal("50000"):
        return "IDV is below the minimum insurable value of 50,000"
    if risk.prior_claims_count is not None and risk.prior_claims_count > 3:
        return "More than 3 prior claims"
    return None


def _evaluate_refer_rules(risk: Risk) -> str | None:
    """Ordered refer rules, checked only when no decline rule matched."""

    if risk.prior_claims_count is not None and risk.prior_claims_count == 3:
        return "Exactly 3 prior claims requires underwriter review"
    if risk.idv is not None and risk.idv > Decimal("1500000"):
        return "IDV above 1,500,000 requires underwriter review"
    return None


def auto_screen_appetite(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: auto_screen_appetite (REQ-005, REQ-006). Ordered decline/refer
    rules, first match wins, with no added human review step."""

    session = ctx["session"]
    publisher: EventPublisher = ctx["publisher"]
    lead_id: str = ctx["lead_id"]

    leads = LeadRepository(session)
    risks = RiskRepository(session)
    lead = _require_lead(leads, lead_id)
    risk = risks.latest_for_lead(lead_id)
    if risk is None or not risk.is_complete:
        raise ValidationFailedError("risk data must be complete before appetite screening")
    if risk.appetite_outcome is not None:
        raise ConflictError("this risk has already been screened")

    previous_status = lead.status
    decline_reason = _evaluate_decline_rules(risk)
    if decline_reason is not None:
        risk.appetite_outcome = AppetiteOutcome.DECLINE
        risk.appetite_reason = decline_reason
        risk.decline_reason = decline_reason
        lead.status = LeadStatus.LOST
        lead.lost_reason = decline_reason
        publisher.lead_status_changed(
            lead.lead_id, previous_status.value, lead.status.value, decline_reason
        )
        return risk_to_dict(risk, lead.status.value, [])

    refer_reason = _evaluate_refer_rules(risk)
    if refer_reason is not None:
        risk.appetite_outcome = AppetiteOutcome.REFER
        risk.appetite_reason = refer_reason
        lead.status = LeadStatus.REFERRED
        publisher.lead_status_changed(lead.lead_id, previous_status.value, lead.status.value)
        return risk_to_dict(risk, lead.status.value, [])

    risk.appetite_outcome = AppetiteOutcome.CLEAR
    risk.is_approved = True
    risk.approved_at = datetime.utcnow()
    lead.status = LeadStatus.APPROVED
    publisher.lead_status_changed(lead.lead_id, previous_status.value, lead.status.value)
    return risk_to_dict(risk, lead.status.value, [])


def record_underwriter_outcome(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: record_underwriter_outcome (REQ-008). Decline sets the lead
    Lost with reason 'Underwriter declined'; approve/approve-with-loading
    stores the risk as the latest approved risk and automatically chains to
    auto_rate_quote (REQ-009's 'no added review step')."""

    session = ctx["session"]
    publisher: EventPublisher = ctx["publisher"]
    lead_id: str = ctx["lead_id"]
    outcome: str = ctx["outcome"]
    loading_percent: Decimal | None = ctx.get("loading_percent")

    leads = LeadRepository(session)
    risks = RiskRepository(session)
    lead = _require_lead(leads, lead_id)
    risk = risks.latest_for_lead(lead_id)
    if risk is None or risk.appetite_outcome != AppetiteOutcome.REFER or lead.status != LeadStatus.REFERRED:
        raise ConflictError("lead is not awaiting an underwriter decision")

    previous_status = lead.status
    if outcome == "Declined":
        risk.underwriter_outcome = UnderwriterOutcome.DECLINED
        risk.decline_reason = "Underwriter declined"
        lead.status = LeadStatus.LOST
        lead.lost_reason = "Underwriter declined"
        publisher.lead_status_changed(
            lead.lead_id, previous_status.value, lead.status.value, "Underwriter declined"
        )
        return risk_to_dict(risk, lead.status.value, [])

    if outcome == "ApprovedWithLoading" and loading_percent is None:
        raise ValidationFailedError("loading_percent is required for ApprovedWithLoading")

    risk.underwriter_outcome = (
        UnderwriterOutcome.APPROVED_WITH_LOADING
        if outcome == "ApprovedWithLoading"
        else UnderwriterOutcome.APPROVED
    )
    risk.loading_percent = loading_percent if outcome == "ApprovedWithLoading" else Decimal("0")
    risk.is_approved = True
    risk.approved_at = datetime.utcnow()
    lead.status = LeadStatus.APPROVED
    publisher.lead_status_changed(lead.lead_id, previous_status.value, lead.status.value)

    quote_context = {"session": session, "publisher": publisher, "lead_id": lead_id}
    quote_result = run_transition("record_underwriter_outcome", "auto_rate_quote", quote_context)

    result = risk_to_dict(risk, lead.status.value, [])
    result["quote"] = quote_result
    return result


register_handler("capture_risk_data", capture_risk_data)
register_handler("auto_screen_appetite", auto_screen_appetite)
register_handler("record_underwriter_outcome", record_underwriter_outcome)
