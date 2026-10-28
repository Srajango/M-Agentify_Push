"""Agent contact activity logging — node: record_contact_activity."""

from __future__ import annotations

from typing import Any

from lead_domain.exceptions import NotFoundError
from lead_domain.mappers import activity_to_dict
from lead_domain.models import Activity, ContactChannel, ContactOutcome
from lead_domain.process_graph import register_handler
from lead_domain.repositories import ActivityRepository, AgentRepository, LeadRepository
from lead_domain.schemas import ActivityCreateRequest


def record_contact_activity(ctx: dict[str, Any]) -> dict[str, Any]:
    """Node: record_contact_activity (REQ-011). Append-only: this is the
    only place an Activity row is ever created — no router exposes an
    update or delete for it, so a logged activity can never be edited or
    deleted."""

    session = ctx["session"]
    lead_id: str = ctx["lead_id"]
    payload: ActivityCreateRequest = ctx["payload"]

    leads = LeadRepository(session)
    agents = AgentRepository(session)
    activities = ActivityRepository(session)
    lead = leads.get(lead_id)
    if lead is None:
        raise NotFoundError(f"lead '{lead_id}' not found")
    agent = agents.get(payload.agent_id)
    if agent is None:
        raise NotFoundError(f"agent '{payload.agent_id}' not found")

    activity = Activity(
        lead_id=lead_id,
        agent_id=payload.agent_id,
        channel=ContactChannel(payload.channel),
        outcome=ContactOutcome(payload.outcome),
        note=payload.note,
        next_follow_up_date=payload.next_follow_up_date,
    )
    activities.add(activity)
    return activity_to_dict(activity)


register_handler("record_contact_activity", record_contact_activity)
