"""Node and routing functions for every step in the lead-to-policy graph.

Each node is an ``async def node_x(state, ctx) -> dict`` that returns a
partial ``RunState`` update (never an empty ``{}`` — every node re-emits at
least ``current_node`` so a structural edge after it never receives an
empty write). Each decision step pairs a node (which may perform the domain
call tied to one of its outgoing edges) with a pure ``route_x(state) -> str``
function used in ``add_conditional_edges`` — this is what ``graph.py`` wires
up so the two outcomes of every branch point to different targets.

The mapping from the 18 consumed operations to the node that calls them
follows the ``derived_from: {"kind": "edge", "ref": "<source>-><target>"}``
metadata in the frozen contract slice: each op fires inside the SOURCE node
of the edge it was derived from, immediately before that node's output
decides which branch to take.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass
from typing import Any

from .domain_client import DomainClient
from .events import (
    EVENT_ACCESS_REPORT_STARTED,
    EVENT_AGENT_ASSIGNED,
    EVENT_AGENT_MANAGEMENT_STARTED,
    EVENT_LEAD_FLOW_STARTED,
    EVENT_LEAD_LOST,
    EVENT_POLICY_ISSUED,
    EVENT_QUOTE_ISSUED,
    EVENT_REASSIGNMENT_STARTED,
    EventPublisher,
)
from .exceptions import ValidationError
from .state import RunState


@dataclass
class NodeContext:
    """Dependencies every node closes over: the domain client and event bus."""

    client: DomainClient
    events: EventPublisher


def _parse_date(value: Any) -> datetime.date | None:
    if not value:
        return None
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# start: dispatches to one of the four sub-flows this orchestrator owns.
# ---------------------------------------------------------------------------

async def node_start(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    dispatch_events = {
        "lead": EVENT_LEAD_FLOW_STARTED,
        "agent_management": EVENT_AGENT_MANAGEMENT_STARTED,
        "reassignment": EVENT_REASSIGNMENT_STARTED,
        "access_report": EVENT_ACCESS_REPORT_STARTED,
    }
    run_type = state.get("run_type", "lead")
    ctx.events.publish(dispatch_events.get(run_type, EVENT_LEAD_FLOW_STARTED), state["run_id"], {"run_type": run_type})
    return {"current_node": "start"}


def route_start(state: RunState) -> str:
    return state.get("run_type", "lead")


# ---------------------------------------------------------------------------
# Main lead pipeline.
# ---------------------------------------------------------------------------

async def node_register_lead(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    lead = state.get("lead", {})
    response = await ctx.client.register_lead(lead)
    return {
        "current_node": "register_lead",
        "lead_id": response.get("lead_id", lead.get("lead_id")),
        "duplicate_found": bool(response.get("duplicate_found", False)),
    }


async def node_check_duplicate(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    return {"current_node": "check_duplicate"}


def route_check_duplicate(state: RunState) -> str:
    return "yes" if state.get("duplicate_found") else "no"


async def node_duplicate_declined(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    ctx.events.publish(
        EVENT_LEAD_LOST, state["run_id"], {"lead_id": state.get("lead_id"), "reason": "Duplicate lead"}
    )
    return {
        "current_node": "duplicate_declined",
        "status": "completed",
        "lost_reason": "Duplicate lead",
        "result": {"outcome": "duplicate_declined"},
    }


async def node_auto_assign_agent(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    lead = state.get("lead", {})
    city = lead.get("city", "")
    await ctx.client.lookup_agent_directory(city)
    response = await ctx.client.auto_assign_agent(state["lead_id"], city)
    assigned = bool(response.get("assigned", False))
    return {
        "current_node": "auto_assign_agent",
        "agent_available_in_city": assigned,
        "assigned_agent_id": response.get("agent_id") if assigned else None,
    }


async def node_check_agent_available(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    if state.get("agent_available_in_city"):
        agent_id = state.get("assigned_agent_id")
        await ctx.client.finalize_auto_assignment(state["lead_id"], agent_id)
        ctx.events.publish(
            EVENT_AGENT_ASSIGNED, state["run_id"], {"lead_id": state.get("lead_id"), "agent_id": agent_id}
        )
    return {"current_node": "check_agent_available"}


def route_check_agent_available(state: RunState) -> str:
    return "yes" if state.get("agent_available_in_city") else "no"


async def node_manager_manual_assign(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    """Human gate: Manager Assigns Agent From Queue (REQ-003).

    This node only runs once the gate's resume operation has set
    ``chosen_agent_id`` on the state (via ``update_state``) and the graph is
    re-invoked; LangGraph's ``interrupt_before`` keeps the run halted here
    until that happens, so the assignment below is applied exactly once.
    """

    agent_id = state.get("chosen_agent_id")
    if not agent_id:
        raise ValidationError("manager_manual_assign resume requires a chosen_agent_id")
    await ctx.client.apply_manual_assignment(state["lead_id"], agent_id)
    ctx.events.publish(
        EVENT_AGENT_ASSIGNED, state["run_id"], {"lead_id": state.get("lead_id"), "agent_id": agent_id}
    )
    return {"current_node": "manager_manual_assign", "assigned_agent_id": agent_id}


async def node_capture_risk_data(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    return {"current_node": "capture_risk_data"}


async def node_check_risk_complete(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    response = await ctx.client.lookup_risk(state["lead_id"])
    complete = bool(response.get("complete", False))
    if not complete:
        await ctx.client.notify_risk_incomplete(state["lead_id"], response.get("missing_fields", []))
    return {"current_node": "check_risk_complete", "risk_complete": complete}


def route_check_risk_complete(state: RunState) -> str:
    return "yes" if state.get("risk_complete") else "no"


async def node_auto_screen_appetite(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    response = await ctx.client.screen_appetite(state["lead_id"], state.get("risk_data", {}))
    return {"current_node": "auto_screen_appetite", "screen_outcome": response.get("outcome", "accept")}


async def node_check_screen_outcome_decline(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    return {"current_node": "check_screen_outcome_decline"}


def route_check_screen_outcome_decline(state: RunState) -> str:
    return "yes" if state.get("screen_outcome") == "decline" else "no"


async def node_lead_lost_decline_screen(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    ctx.events.publish(
        EVENT_LEAD_LOST,
        state["run_id"],
        {"lead_id": state.get("lead_id"), "reason": "Declined by screening"},
    )
    return {
        "current_node": "lead_lost_decline_screen",
        "status": "completed",
        "lost_reason": "Declined by screening",
        "result": {"outcome": "lead_lost"},
    }


async def node_check_screen_outcome_refer(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    return {"current_node": "check_screen_outcome_refer"}


def route_check_screen_outcome_refer(state: RunState) -> str:
    return "yes" if state.get("screen_outcome") == "refer" else "no"


async def node_underwriter_review_referral(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    """Human gate: Underwriter Decides On Referred Risk (REQ-007).

    Runs only once the resume/reject endpoint has set ``underwriter_decision``
    on the state and the graph is re-invoked; the gate node itself makes no
    domain call -- the outcome-specific calls happen downstream in
    ``record_underwriter_outcome`` or ``lead_lost_underwriter_decline``.
    """

    decision = state.get("underwriter_decision")
    if decision not in ("approve", "approve_with_loading", "decline"):
        raise ValidationError("underwriter_review_referral resume requires a valid underwriter_decision")
    return {"current_node": "underwriter_review_referral"}


async def node_check_underwriter_decision(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    return {"current_node": "check_underwriter_decision"}


def route_check_underwriter_decision(state: RunState) -> str:
    return "yes" if state.get("underwriter_decision") == "decline" else "no"


async def node_lead_lost_underwriter_decline(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    ctx.events.publish(
        EVENT_LEAD_LOST,
        state["run_id"],
        {"lead_id": state.get("lead_id"), "reason": "Underwriter declined"},
    )
    return {
        "current_node": "lead_lost_underwriter_decline",
        "status": "completed",
        "lost_reason": "Underwriter declined",
        "result": {"outcome": "lead_lost"},
    }


async def node_record_underwriter_outcome(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    decision = state.get("underwriter_decision", "approve")
    await ctx.client.record_underwriter_outcome(state["lead_id"], decision)
    return {"current_node": "record_underwriter_outcome"}


async def node_auto_rate_quote(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    response = await ctx.client.rate_quote(state["lead_id"], state.get("risk_data", {}))
    quote = {
        "quote_id": response.get("quote_id"),
        "total": response.get("total"),
        "expiry": response.get("expiry"),
    }
    ctx.events.publish(
        EVENT_QUOTE_ISSUED, state["run_id"], {"lead_id": state.get("lead_id"), "quote_id": quote["quote_id"]}
    )
    return {"current_node": "auto_rate_quote", "quote": quote}


async def node_record_contact_activity(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    # No consumed operation is tied to this node's edges in the frozen
    # contract slice; the re-rate trigger is read straight from the lead
    # payload as a bounded count (see GAPS.json -- no field for it was
    # verified at Gate 3). ``rerate_count`` threads through the loop so the
    # decision flips to "no" once the requested number of re-rates ran,
    # rather than looping on a static flag forever.
    requested = int(state.get("lead", {}).get("rerate_requested_count", 0))
    done = int(state.get("rerate_count", 0))
    return {"current_node": "record_contact_activity", "rerate": done < requested}


async def node_agent_rerate_decision(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    if state.get("rerate"):
        await ctx.client.flag_rerate(state["lead_id"])
        return {
            "current_node": "agent_rerate_decision",
            "rerate_count": int(state.get("rerate_count", 0)) + 1,
        }
    return {"current_node": "agent_rerate_decision"}


def route_agent_rerate_decision(state: RunState) -> str:
    return "yes" if state.get("rerate") else "no"


async def node_client_decision_wait(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    await ctx.client.fetch_latest_quote_for_wait(state["lead_id"])
    response = await ctx.client.fetch_client_decision(state["lead_id"])
    return {"current_node": "client_decision_wait", "client_outcome": response.get("client_outcome", "accept")}


async def node_check_client_outcome_accept(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    return {"current_node": "check_client_outcome_accept"}


def route_check_client_outcome_accept(state: RunState) -> str:
    return "yes" if state.get("client_outcome") == "accept" else "no"


async def node_check_client_outcome_decline(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    return {"current_node": "check_client_outcome_decline"}


def route_check_client_outcome_decline(state: RunState) -> str:
    return "yes" if state.get("client_outcome") == "decline" else "no"


async def node_lead_lost_client_decline(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    reason = state.get("client_decline_reason") or "Client declined"
    ctx.events.publish(EVENT_LEAD_LOST, state["run_id"], {"lead_id": state.get("lead_id"), "reason": reason})
    return {
        "current_node": "lead_lost_client_decline",
        "status": "completed",
        "lost_reason": reason,
        "result": {"outcome": "lead_lost"},
    }


async def node_lead_lost_quote_expired(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    ctx.events.publish(
        EVENT_LEAD_LOST, state["run_id"], {"lead_id": state.get("lead_id"), "reason": "Quote expired"}
    )
    return {
        "current_node": "lead_lost_quote_expired",
        "status": "completed",
        "lost_reason": "Quote expired",
        "result": {"outcome": "lead_lost"},
    }


async def node_validate_bind_inputs(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    quote_resp = await ctx.client.fetch_quote_for_bind(state["lead_id"])
    bind_inputs = state.get("bind_inputs", {})
    effective_date = _parse_date(bind_inputs.get("effective_date"))
    amount_collected = bind_inputs.get("amount_collected")
    quote_total = quote_resp.get("total")
    expiry_date = _parse_date(quote_resp.get("expiry"))

    errors: list[str] = []
    if effective_date is None:
        errors.append("effective_date is required and must be a valid date")
    else:
        today = datetime.date.today()
        if effective_date < today:
            errors.append("effective_date must be on or after today")
        if expiry_date is not None and effective_date > expiry_date:
            errors.append("effective_date must be on or before the quote expiry date")
    if amount_collected is None:
        errors.append("amount_collected is required")
    elif quote_total is not None and float(amount_collected) != float(quote_total):
        errors.append("amount_collected must equal the quote total of the latest version")

    if errors:
        raise ValidationError("; ".join(errors))

    return {
        "current_node": "validate_bind_inputs",
        "quote": {**state.get("quote", {}), "total": quote_total, "expiry": quote_resp.get("expiry")},
    }


async def node_bind_and_issue_policy(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    policy_number = f"PC-{datetime.date.today().year}-{uuid.uuid4().int % 1_000_000:06d}"
    policy = {
        "policy_number": policy_number,
        "coverage": state.get("quote", {}),
        "effective_date": state.get("bind_inputs", {}).get("effective_date"),
    }
    ctx.events.publish(
        EVENT_POLICY_ISSUED,
        state["run_id"],
        {"lead_id": state.get("lead_id"), "policy_number": policy_number},
    )
    return {"current_node": "bind_and_issue_policy", "policy": policy}


async def node_end_converted(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    return {
        "current_node": "end_converted",
        "status": "completed",
        "result": {"outcome": "converted", "policy": state.get("policy", {})},
    }


# ---------------------------------------------------------------------------
# Side flows: agent management, reassignment, access & reporting.
# ---------------------------------------------------------------------------

async def node_manage_agent_records(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    agent_record = state.get("agent_record", {})
    response = await ctx.client.upsert_agent_record(agent_record)
    return {"current_node": "manage_agent_records", "agent_record": {**agent_record, **response}}


async def node_manager_reassign_lead(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    reassignment = state.get("reassignment", {})
    await ctx.client.reassign_lead(reassignment.get("lead_id", ""), reassignment.get("new_agent_id", ""))
    ctx.events.publish(
        EVENT_AGENT_ASSIGNED,
        state["run_id"],
        {"lead_id": reassignment.get("lead_id"), "agent_id": reassignment.get("new_agent_id")},
    )
    return {"current_node": "manager_reassign_lead"}


async def node_end_reassign(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    return {"current_node": "end_reassign", "status": "completed", "result": {"outcome": "reassigned"}}


async def node_role_based_access_control(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    access_report = state.get("access_report", {})
    lead_id = access_report.get("lead_id") or state.get("lead_id")
    lead_resp = await ctx.client.lookup_lead(lead_id) if lead_id else {}
    return {"current_node": "role_based_access_control", "access_report": {**access_report, "lead": lead_resp}}


async def node_compute_counts_conversion(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    access_report = state.get("access_report", {})
    counts = {"lead_id": access_report.get("lead_id"), "role": access_report.get("role")}
    await ctx.client.publish_counts(counts)
    return {"current_node": "compute_counts_conversion", "access_report": {**access_report, "counts": counts}}


async def node_end_access_counts(state: RunState, ctx: NodeContext) -> dict[str, Any]:
    return {
        "current_node": "end_access_counts",
        "status": "completed",
        "result": {"outcome": "access_and_reporting_available"},
    }
