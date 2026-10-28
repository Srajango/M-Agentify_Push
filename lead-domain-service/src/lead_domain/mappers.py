"""Converts ORM rows into the plain dicts the Pydantic response schemas
validate, resolving every Enum column to its plain string value explicitly
(never relying on implicit str-subclass JSON serialization)."""

from __future__ import annotations

from lead_domain.models import Activity, Agent, Lead, Policy, Quote, Risk


def agent_to_dict(agent: Agent) -> dict:
    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "city": agent.city,
        "active": agent.active,
    }


def lead_to_dict(lead: Lead) -> dict:
    return {
        "lead_id": lead.lead_id,
        "customer_name": lead.customer_name,
        "mobile_number": lead.mobile_number,
        "email": lead.email,
        "city": lead.city,
        "source": lead.source,
        "product": lead.product,
        "vehicle_registration_number": lead.vehicle_registration_number,
        "status": lead.status.value,
        "agent_id": lead.agent_id,
        "lost_reason": lead.lost_reason,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
    }


def risk_to_dict(risk: Risk, lead_status: str, missing_fields: list[str]) -> dict:
    return {
        "risk_id": risk.risk_id,
        "lead_id": risk.lead_id,
        "vehicle_make": risk.vehicle_make,
        "vehicle_model": risk.vehicle_model,
        "registration_year": risk.registration_year,
        "idv": risk.idv,
        "coverage_type": risk.coverage_type.value if risk.coverage_type else None,
        "no_claim_bonus_fraction": risk.no_claim_bonus_fraction,
        "prior_claims_count": risk.prior_claims_count,
        "is_complete": risk.is_complete,
        "missing_fields": missing_fields,
        "appetite_outcome": risk.appetite_outcome.value if risk.appetite_outcome else None,
        "appetite_reason": risk.appetite_reason,
        "underwriter_outcome": risk.underwriter_outcome.value if risk.underwriter_outcome else None,
        "loading_percent": risk.loading_percent,
        "decline_reason": risk.decline_reason,
        "is_approved": risk.is_approved,
        "lead_status": lead_status,
    }


def quote_to_dict(quote: Quote, lead_status: str) -> dict:
    return {
        "quote_id": quote.quote_id,
        "lead_id": quote.lead_id,
        "risk_id": quote.risk_id,
        "version": quote.version,
        "coverage_type": quote.coverage_type.value,
        "idv": quote.idv,
        "own_damage_premium": quote.own_damage_premium,
        "third_party_premium": quote.third_party_premium,
        "no_claim_bonus_amount": quote.no_claim_bonus_amount,
        "loading_amount": quote.loading_amount,
        "total_premium": quote.total_premium,
        "status": quote.status.value,
        "rated_at": quote.rated_at,
        "expires_at": quote.expires_at,
        "lead_status": lead_status,
    }


def activity_to_dict(activity: Activity) -> dict:
    return {
        "activity_id": activity.activity_id,
        "lead_id": activity.lead_id,
        "agent_id": activity.agent_id,
        "channel": activity.channel.value,
        "outcome": activity.outcome.value,
        "note": activity.note,
        "next_follow_up_date": activity.next_follow_up_date,
        "occurred_at": activity.occurred_at,
    }


def policy_to_dict(policy: Policy, lead_status: str) -> dict:
    return {
        "policy_number": policy.policy_number,
        "lead_id": policy.lead_id,
        "lead_status": lead_status,
        "coverage_type": policy.coverage_type.value,
        "idv": policy.idv,
        "premium_breakdown": policy.premium_breakdown,
        "no_claim_bonus_amount": policy.no_claim_bonus_amount,
        "loading_amount": policy.loading_amount,
        "effective_date": policy.effective_date,
        "issued_at": policy.issued_at,
    }
