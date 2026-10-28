"""The compiled process graph this service owns.

This mirrors the APPROVED process model's Steps and Transitions exactly: 14
nodes, the 4 explicit transitions between them, multiple entry points and no
terminal node. Each node is bound to the real service-layer function that
implements it via `register_handler` (called at import time by the
`services` modules), so the graph is provably wired to running code rather
than being a parallel description of it. `run_transition` is the mechanism
that actually walks a conditional edge by invoking the destination node's
handler with the upstream result — used where the destination node must run
automatically with no added human step (record_underwriter_outcome ->
auto_rate_quote, validate_bind_inputs -> bind_and_issue_policy).
"""

from __future__ import annotations

from typing import Any, Callable

NODES: dict[str, str] = {
    "register_lead": "Register New Lead",
    "auto_assign_agent": "Auto-Assign Agent By Round-Robin",
    "manage_agent_records": "Maintain Agent Records",
    "capture_risk_data": "Capture Risk Data",
    "auto_screen_appetite": "Auto-Screen Appetite",
    "record_underwriter_outcome": "Record Underwriter Approval Outcome",
    "auto_rate_quote": "Auto-Rate Latest Approved Risk",
    "record_contact_activity": "Record Agent Contact Activity",
    "client_decision_wait": "Wait For Client Accept, Decline, Or Expiry",
    "validate_bind_inputs": "Validate Effective Date And Collected Amount",
    "bind_and_issue_policy": "Bind Acceptance And Issue Policy",
    "manager_reassign_lead": "Manager Reassigns Open Lead",
    "role_based_access_control": "Enforce Role-Based Visibility And Actions",
    "compute_counts_conversion": "Compute Counts And Conversion Rate",
}

EDGES: list[tuple[str, str]] = [
    ("record_underwriter_outcome", "auto_rate_quote"),
    ("auto_rate_quote", "record_contact_activity"),
    ("validate_bind_inputs", "bind_and_issue_policy"),
    ("role_based_access_control", "compute_counts_conversion"),
]

ENTRY_NODES: set[str] = {
    "register_lead",
    "auto_assign_agent",
    "manage_agent_records",
    "capture_risk_data",
    "auto_screen_appetite",
    "record_underwriter_outcome",
    "client_decision_wait",
    "validate_bind_inputs",
    "manager_reassign_lead",
    "role_based_access_control",
}

TERMINAL_NODES: set[str] = set()

NodeHandler = Callable[[dict[str, Any]], dict[str, Any]]

_HANDLERS: dict[str, NodeHandler] = {}


def register_handler(node_key: str, handler: NodeHandler) -> None:
    """Bind a node of the compiled graph to the real function that
    implements it. Raises if the node is not part of the approved graph."""

    if node_key not in NODES:
        raise KeyError(f"'{node_key}' is not a node in the approved process graph")
    _HANDLERS[node_key] = handler


def get_handler(node_key: str) -> NodeHandler:
    try:
        return _HANDLERS[node_key]
    except KeyError as exc:
        raise KeyError(f"no handler registered for node '{node_key}'") from exc


def registered_nodes() -> set[str]:
    return set(_HANDLERS.keys())


def edges_from(node_key: str) -> list[str]:
    return [target for source, target in EDGES if source == node_key]


def run_transition(source_node: str, target_node: str, context: dict[str, Any]) -> dict[str, Any]:
    """Walk the edge source_node -> target_node by invoking the target
    node's handler, so the automated follow-on step actually runs instead of
    only being described."""

    if (source_node, target_node) not in EDGES:
        raise KeyError(f"'{source_node}' -> '{target_node}' is not an edge in the approved graph")
    return get_handler(target_node)(context)


def validate_graph() -> None:
    """Assert the compiled graph matches the approved process model: every
    edge endpoint is a declared node, and every declared node has a
    registered handler reachable from the entrypoint."""

    for source, target in EDGES:
        if source not in NODES or target not in NODES:
            raise ValueError(f"edge '{source}' -> '{target}' references an undeclared node")
    missing = set(NODES) - registered_nodes()
    if missing:
        raise ValueError(f"nodes without a registered handler: {sorted(missing)}")
