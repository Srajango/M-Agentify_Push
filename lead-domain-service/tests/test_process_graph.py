"""The compiled graph must match the approved process model exactly: 14
nodes, the 4 declared transitions, no terminal node."""

from __future__ import annotations

import pytest

from lead_domain import services  # noqa: F401
from lead_domain.process_graph import EDGES, ENTRY_NODES, NODES, TERMINAL_NODES, edges_from, validate_graph


def test_graph_has_exactly_the_approved_nodes() -> None:
    assert set(NODES) == {
        "register_lead",
        "auto_assign_agent",
        "manage_agent_records",
        "capture_risk_data",
        "auto_screen_appetite",
        "record_underwriter_outcome",
        "auto_rate_quote",
        "record_contact_activity",
        "client_decision_wait",
        "validate_bind_inputs",
        "bind_and_issue_policy",
        "manager_reassign_lead",
        "role_based_access_control",
        "compute_counts_conversion",
    }


def test_graph_has_exactly_the_approved_transitions() -> None:
    assert set(EDGES) == {
        ("record_underwriter_outcome", "auto_rate_quote"),
        ("auto_rate_quote", "record_contact_activity"),
        ("validate_bind_inputs", "bind_and_issue_policy"),
        ("role_based_access_control", "compute_counts_conversion"),
    }


def test_graph_has_no_terminal_node() -> None:
    assert TERMINAL_NODES == set()


def test_graph_has_ten_entry_nodes() -> None:
    assert ENTRY_NODES == {
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


def test_validate_graph_passes_once_services_are_imported() -> None:
    validate_graph()


def test_undeclared_edge_is_rejected() -> None:
    from lead_domain.process_graph import run_transition

    with pytest.raises(KeyError, match="not an edge"):
        run_transition("register_lead", "auto_assign_agent", {})


def test_edges_from_reports_each_nodes_outgoing_transitions() -> None:
    assert edges_from("record_underwriter_outcome") == ["auto_rate_quote"]
    assert edges_from("auto_rate_quote") == ["record_contact_activity"]
    assert edges_from("validate_bind_inputs") == ["bind_and_issue_policy"]
    assert edges_from("role_based_access_control") == ["compute_counts_conversion"]
    assert edges_from("manage_agent_records") == []
