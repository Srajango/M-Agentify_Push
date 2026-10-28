"""Structural verification that the compiled graph matches the approved
process model exactly: every node from the Steps list is registered, and no
conditional branch collapses both outcomes onto the same target.
"""

from __future__ import annotations

import inspect
import re

from orchestrator_app import graph as graph_module
from orchestrator_app.config import Settings
from orchestrator_app.domain_client import DomainClient
from orchestrator_app.events import EventPublisher
from orchestrator_app.graph import NODE_NAMES, build_graph


def test_node_map_declares_every_node_name_and_is_registered_via_add_node() -> None:
    source = inspect.getsource(graph_module.build_graph)

    # node_map's keys must be exactly the 34 Steps from the approved process model.
    node_map_block = re.search(r"node_map:.*?=\s*\{(.*?)\n    \}", source, re.DOTALL).group(1)
    declared = set(re.findall(r'"([a-z_]+)":\s*n\.node_', node_map_block))
    assert declared == set(NODE_NAMES), (
        f"missing from node_map: {set(NODE_NAMES) - declared}, "
        f"extra in node_map: {declared - set(NODE_NAMES)}"
    )

    # Every entry in node_map is actually passed to graph.add_node (not dead code).
    assert re.search(r"for name, fn in node_map\.items\(\):\s*\n\s*graph\.add_node\(name,", source)


def test_compiled_graph_contains_every_declared_node() -> None:
    settings = Settings(DRY_RUN=True)
    client = DomainClient(settings)
    compiled = build_graph(client, EventPublisher())
    assert set(NODE_NAMES) <= set(compiled.get_graph().nodes.keys())


def test_no_conditional_branch_collapses_both_outcomes_to_one_target() -> None:
    source = inspect.getsource(graph_module.build_graph)
    mappings = re.findall(r"add_conditional_edges\(\s*\"[a-z_]+\",\s*[a-zA-Z_.]+,\s*\{([^}]+)\}", source)
    assert len(mappings) == 10, f"expected 10 conditional edge blocks, found {len(mappings)}"
    for block in mappings:
        targets = re.findall(r':\s*"([a-z_]+)"', block)
        assert len(set(targets)) > 1, f"conditional mapping routes every outcome to one target: {block}"


def test_both_human_gates_are_wired_with_interrupt_before() -> None:
    source = inspect.getsource(graph_module.build_graph)
    assert "interrupt_before=list(GATE_NODES)" in source
    assert graph_module.GATE_NODES == ("manager_manual_assign", "underwriter_review_referral")
