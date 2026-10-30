"""Role-based visibility and agency reporting counts — nodes:
role_based_access_control, compute_counts_conversion."""

from __future__ import annotations

from typing import Any

from lead_domain.exceptions import ForbiddenError, ValidationFailedError
from lead_domain.mappers import lead_to_dict
from lead_domain.models import LeadStatus
from lead_domain.process_graph import register_handler, run_transition
from lead_domain.repositories import AgentRepository, LeadRepository

ROLES = ("agent", "underwriter", "manager")


def role_based_access_control(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: role_based_access_control (REQ-017). An agent sees only their
    own leads, an underwriter sees the referral queue, a manager sees every
    lead. A manager's listing also chains to compute_counts_conversion."""

    session = ctx["session"]
    role: str = ctx["role"]
    agent_id: str | None = ctx.get("agent_id")

    if role not in ROLES:
        raise ForbiddenError(f"unknown role '{role}'")

    leads = LeadRepository(session)
    if role == "agent":
        if not agent_id:
            raise ValidationFailedError("agent_id is required when role=agent")
        selected = leads.list_by_agent(agent_id)
    elif role == "underwriter":
        selected = leads.list_referred()
    else:
        selected = leads.list_all()

    result: dict[str, Any] = {
        "role": role,
        "leads": [lead_to_dict(lead) for lead in selected],
    }
    if role == "manager":
        result["counts"] = run_transition(
            "role_based_access_control", "compute_counts_conversion", {"session": session}
        )
    return result


def compute_counts_conversion(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: compute_counts_conversion (REQ-018). For each agent and for the
    agency: leads assigned, still open, converted, lost, and the conversion
    rate (converted / assigned), read live from the lead table."""

    session = ctx["session"]
    all_leads = LeadRepository(session).list_all()
    agents = AgentRepository(session).list_all()

    def counts_for(predicate) -> dict[str, int]:
        subset = [lead for lead in all_leads if predicate(lead)]
        return {
            "assigned": len(subset),
            "open": len([l for l in subset if l.status not in (LeadStatus.LOST, LeadStatus.CONVERTED)]),
            "converted": len([l for l in subset if l.status == LeadStatus.CONVERTED]),
            "lost": len([l for l in subset if l.status == LeadStatus.LOST]),
        }

    agent_rows = []
    for agent in agents:
        c = counts_for(lambda lead, aid=agent.agent_id: lead.agent_id == aid)
        rate = (c["converted"] / c["assigned"]) if c["assigned"] else 0.0
        agent_rows.append(
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "assigned": c["assigned"],
                "open": c["open"],
                "converted": c["converted"],
                "lost": c["lost"],
                "conversion_rate": rate,
            }
        )

    agency_counts = counts_for(lambda lead: True)
    agency_rate = (
        (agency_counts["converted"] / agency_counts["assigned"]) if agency_counts["assigned"] else 0.0
    )
    return {
        "agents": agent_rows,
        "agency": {**agency_counts, "conversion_rate": agency_rate},
    }


register_handler("role_based_access_control", role_based_access_control)
register_handler("compute_counts_conversion", compute_counts_conversion)
