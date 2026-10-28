"""Lead registration, round-robin agent assignment, agent roster management,
and manager reassignment — nodes: register_lead, auto_assign_agent,
manage_agent_records, manager_reassign_lead."""

from __future__ import annotations

from typing import Any

from lead_domain.events import EventPublisher
from lead_domain.exceptions import ConflictError, DuplicateLeadError, NotFoundError, ValidationFailedError
from lead_domain.mappers import agent_to_dict, lead_to_dict
from lead_domain.models import Agent, Lead, LeadStatus
from lead_domain.process_graph import register_handler
from lead_domain.repositories import AgentRepository, LeadRepository
from lead_domain.schemas import AgentUpsertRequest, LeadRegisterRequest


def register_lead(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: register_lead (REQ-001, REQ-002)."""

    session = ctx["session"]
    publisher: EventPublisher = ctx["publisher"]
    payload: LeadRegisterRequest = ctx["payload"]

    leads = LeadRepository(session)
    duplicates = leads.list_open_by_mobile_and_vehicle(
        payload.mobile_number, payload.vehicle_registration_number
    )
    if duplicates:
        raise DuplicateLeadError(
            "An open lead already exists for this mobile number and vehicle registration number"
        )

    lead = Lead(
        customer_name=payload.customer_name,
        mobile_number=payload.mobile_number,
        email=payload.email,
        city=payload.city,
        source=payload.source,
        product="Private Car",
        vehicle_registration_number=payload.vehicle_registration_number,
        status=LeadStatus.NEW,
    )
    leads.add(lead)
    publisher.lead_registered(lead.lead_id, lead.status.value)
    return {"lead": lead_to_dict(lead), "lead_id": lead.lead_id}


def _select_round_robin_agent(active_agents: list[Agent], leads: LeadRepository) -> Agent:
    """Among active agents serving the city, pick the one with the fewest
    currently assigned leads (ties broken by agent_id) — a deterministic
    round-robin distribution that needs no persisted rotation counter."""

    def load(agent: Agent) -> tuple[int, str]:
        return (len(leads.list_by_agent(agent.agent_id)), agent.agent_id)

    return min(active_agents, key=load)


def auto_assign_agent(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: auto_assign_agent. Round-robin among active agents in the
    lead's city; a manager-supplied agent_id overrides the round-robin pick
    (REQ covered by task 2's "manager-chosen" assignment path)."""

    session = ctx["session"]
    lead_id: str = ctx["lead_id"]
    manager_agent_id: str | None = ctx.get("manager_agent_id")

    leads = LeadRepository(session)
    agents = AgentRepository(session)
    lead = leads.get(lead_id)
    if lead is None:
        raise NotFoundError(f"lead '{lead_id}' not found")

    if manager_agent_id is not None:
        agent = agents.get(manager_agent_id)
        if agent is None or not agent.active:
            raise ValidationFailedError("manager-chosen agent must be an existing active agent")
        lead.agent_id = agent.agent_id
        return {"lead_id": lead.lead_id, "agent_id": agent.agent_id, "assigned": True}

    if lead.agent_id:
        return {"lead_id": lead.lead_id, "agent_id": lead.agent_id, "assigned": True}

    active_agents = agents.list_active_by_city(lead.city)
    if not active_agents:
        return {"lead_id": lead.lead_id, "agent_id": None, "assigned": False}

    chosen = _select_round_robin_agent(active_agents, leads)
    lead.agent_id = chosen.agent_id
    return {"lead_id": lead.lead_id, "agent_id": chosen.agent_id, "assigned": True}


def manage_agent_records(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: manage_agent_records. Creates a new agent or updates an
    existing one's name, city and active flag (upsert_agent_record,
    op_9fcce42948fc43c0 — frozen)."""

    session = ctx["session"]
    payload: AgentUpsertRequest = ctx["payload"]

    agents = AgentRepository(session)
    if payload.agent_id:
        agent = agents.get(payload.agent_id)
        if agent is None:
            raise NotFoundError(f"agent '{payload.agent_id}' not found")
        agent.name = payload.name
        agent.city = payload.city
        agent.active = payload.active
    else:
        agent = Agent(name=payload.name, city=payload.city, active=payload.active)
        agents.add(agent)
    return agent_to_dict(agent)


def manager_reassign_lead(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: manager_reassign_lead (REQ-016). Rejects a Converted or Lost
    lead; otherwise reassigns to a different active agent, leaving status
    and activity history untouched."""

    session = ctx["session"]
    lead_id: str = ctx["lead_id"]
    new_agent_id: str = ctx["new_agent_id"]

    leads = LeadRepository(session)
    agents = AgentRepository(session)
    lead = leads.get(lead_id)
    if lead is None:
        raise NotFoundError(f"lead '{lead_id}' not found")
    if lead.status in (LeadStatus.CONVERTED, LeadStatus.LOST):
        raise ConflictError(f"a {lead.status.value} lead cannot be reassigned")

    new_agent = agents.get(new_agent_id)
    if new_agent is None or not new_agent.active:
        raise ValidationFailedError("new_agent_id must be an existing active agent")

    lead.agent_id = new_agent.agent_id
    return lead_to_dict(lead)


register_handler("register_lead", register_lead)
register_handler("auto_assign_agent", auto_assign_agent)
register_handler("manage_agent_records", manage_agent_records)
register_handler("manager_reassign_lead", manager_reassign_lead)
