"""Builds and compiles the lead-to-policy LangGraph StateGraph.

Every step in the approved process model is a node here and every
transition is an edge — see the module-level ``NODE_NAMES`` /
``CONDITIONAL_EDGES`` assertions at the bottom, which a test imports to
confirm nothing from the plan's Steps/Transitions list was dropped.

The two human gates (``manager_manual_assign``, ``underwriter_review_referral``)
are wired with ``interrupt_before`` so the compiled graph halts BEFORE
executing them and does not resume until the gate's resume/reject endpoint
updates state and re-invokes the graph with the same thread id.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from . import nodes as n
from .domain_client import DomainClient
from .events import EventPublisher
from .state import RunState

NodeFn = Callable[[RunState], Awaitable[dict[str, Any]]]

GATE_NODES = ("manager_manual_assign", "underwriter_review_referral")


def _bind(fn: Callable[[RunState, n.NodeContext], Awaitable[dict[str, Any]]], ctx: n.NodeContext) -> NodeFn:
    async def _wrapped(state: RunState) -> dict[str, Any]:
        return await fn(state, ctx)

    _wrapped.__name__ = fn.__name__
    return _wrapped


def build_graph(client: DomainClient, events: EventPublisher) -> Any:
    """Compile the full 34-node graph with an in-memory checkpointer.

    Returns the compiled graph (a ``CompiledStateGraph``); callers invoke it
    with ``{"configurable": {"thread_id": run_id}}`` so each run gets its own
    persisted checkpoint and can be paused/resumed independently.
    """

    ctx = n.NodeContext(client=client, events=events)
    graph = StateGraph(RunState)

    node_map: dict[str, Callable[[RunState, n.NodeContext], Awaitable[dict[str, Any]]]] = {
        "start": n.node_start,
        "register_lead": n.node_register_lead,
        "check_duplicate": n.node_check_duplicate,
        "duplicate_declined": n.node_duplicate_declined,
        "auto_assign_agent": n.node_auto_assign_agent,
        "check_agent_available": n.node_check_agent_available,
        "manager_manual_assign": n.node_manager_manual_assign,
        "manage_agent_records": n.node_manage_agent_records,
        "capture_risk_data": n.node_capture_risk_data,
        "check_risk_complete": n.node_check_risk_complete,
        "auto_screen_appetite": n.node_auto_screen_appetite,
        "check_screen_outcome_decline": n.node_check_screen_outcome_decline,
        "lead_lost_decline_screen": n.node_lead_lost_decline_screen,
        "check_screen_outcome_refer": n.node_check_screen_outcome_refer,
        "underwriter_review_referral": n.node_underwriter_review_referral,
        "check_underwriter_decision": n.node_check_underwriter_decision,
        "lead_lost_underwriter_decline": n.node_lead_lost_underwriter_decline,
        "record_underwriter_outcome": n.node_record_underwriter_outcome,
        "auto_rate_quote": n.node_auto_rate_quote,
        "record_contact_activity": n.node_record_contact_activity,
        "agent_rerate_decision": n.node_agent_rerate_decision,
        "client_decision_wait": n.node_client_decision_wait,
        "check_client_outcome_accept": n.node_check_client_outcome_accept,
        "check_client_outcome_decline": n.node_check_client_outcome_decline,
        "lead_lost_client_decline": n.node_lead_lost_client_decline,
        "lead_lost_quote_expired": n.node_lead_lost_quote_expired,
        "validate_bind_inputs": n.node_validate_bind_inputs,
        "bind_and_issue_policy": n.node_bind_and_issue_policy,
        "manager_reassign_lead": n.node_manager_reassign_lead,
        "role_based_access_control": n.node_role_based_access_control,
        "compute_counts_conversion": n.node_compute_counts_conversion,
        "end_converted": n.node_end_converted,
        "end_reassign": n.node_end_reassign,
        "end_access_counts": n.node_end_access_counts,
    }

    for name, fn in node_map.items():
        graph.add_node(name, _bind(fn, ctx))

    graph.set_entry_point("start")

    graph.add_conditional_edges(
        "start",
        n.route_start,
        {
            "lead": "register_lead",
            "agent_management": "manage_agent_records",
            "reassignment": "manager_reassign_lead",
            "access_report": "role_based_access_control",
        },
    )

    graph.add_edge("register_lead", "check_duplicate")
    graph.add_conditional_edges(
        "check_duplicate",
        n.route_check_duplicate,
        {"yes": "duplicate_declined", "no": "auto_assign_agent"},
    )
    graph.add_edge("duplicate_declined", END)

    graph.add_edge("auto_assign_agent", "check_agent_available")
    graph.add_conditional_edges(
        "check_agent_available",
        n.route_check_agent_available,
        {"yes": "capture_risk_data", "no": "manager_manual_assign"},
    )

    graph.add_edge("manager_manual_assign", "capture_risk_data")

    graph.add_edge("capture_risk_data", "check_risk_complete")
    graph.add_conditional_edges(
        "check_risk_complete",
        n.route_check_risk_complete,
        {"no": "capture_risk_data", "yes": "auto_screen_appetite"},
    )

    graph.add_edge("auto_screen_appetite", "check_screen_outcome_decline")
    graph.add_conditional_edges(
        "check_screen_outcome_decline",
        n.route_check_screen_outcome_decline,
        {"yes": "lead_lost_decline_screen", "no": "check_screen_outcome_refer"},
    )
    graph.add_edge("lead_lost_decline_screen", END)

    graph.add_conditional_edges(
        "check_screen_outcome_refer",
        n.route_check_screen_outcome_refer,
        {"yes": "underwriter_review_referral", "no": "auto_rate_quote"},
    )

    graph.add_edge("underwriter_review_referral", "check_underwriter_decision")
    graph.add_conditional_edges(
        "check_underwriter_decision",
        n.route_check_underwriter_decision,
        {"yes": "lead_lost_underwriter_decline", "no": "record_underwriter_outcome"},
    )
    graph.add_edge("lead_lost_underwriter_decline", END)

    graph.add_edge("record_underwriter_outcome", "auto_rate_quote")
    graph.add_edge("auto_rate_quote", "record_contact_activity")
    graph.add_edge("record_contact_activity", "agent_rerate_decision")
    graph.add_conditional_edges(
        "agent_rerate_decision",
        n.route_agent_rerate_decision,
        {"yes": "capture_risk_data", "no": "client_decision_wait"},
    )

    graph.add_edge("client_decision_wait", "check_client_outcome_accept")
    graph.add_conditional_edges(
        "check_client_outcome_accept",
        n.route_check_client_outcome_accept,
        {"yes": "validate_bind_inputs", "no": "check_client_outcome_decline"},
    )
    graph.add_conditional_edges(
        "check_client_outcome_decline",
        n.route_check_client_outcome_decline,
        {"yes": "lead_lost_client_decline", "no": "lead_lost_quote_expired"},
    )
    graph.add_edge("lead_lost_client_decline", END)
    graph.add_edge("lead_lost_quote_expired", END)

    graph.add_edge("validate_bind_inputs", "bind_and_issue_policy")
    graph.add_edge("bind_and_issue_policy", "end_converted")
    graph.add_edge("end_converted", END)

    graph.add_edge("manage_agent_records", "end_access_counts")
    graph.add_edge("manager_reassign_lead", "end_reassign")
    graph.add_edge("end_reassign", END)
    graph.add_edge("role_based_access_control", "compute_counts_conversion")
    graph.add_edge("compute_counts_conversion", "end_access_counts")
    graph.add_edge("end_access_counts", END)

    return graph.compile(checkpointer=MemorySaver(), interrupt_before=list(GATE_NODES))


# Every node name declared in the approved process model's Steps list, used by
# tests/test_graph_wiring.py to assert none were dropped from the compiled graph.
NODE_NAMES: tuple[str, ...] = (
    "start", "register_lead", "check_duplicate", "duplicate_declined",
    "auto_assign_agent", "check_agent_available", "manager_manual_assign",
    "manage_agent_records", "capture_risk_data", "check_risk_complete",
    "auto_screen_appetite", "check_screen_outcome_decline", "lead_lost_decline_screen",
    "check_screen_outcome_refer", "underwriter_review_referral", "check_underwriter_decision",
    "lead_lost_underwriter_decline", "record_underwriter_outcome", "auto_rate_quote",
    "record_contact_activity", "agent_rerate_decision", "client_decision_wait",
    "check_client_outcome_accept", "check_client_outcome_decline", "lead_lost_client_decline",
    "lead_lost_quote_expired", "validate_bind_inputs", "bind_and_issue_policy",
    "manager_reassign_lead", "role_based_access_control", "compute_counts_conversion",
    "end_converted", "end_reassign", "end_access_counts",
)
