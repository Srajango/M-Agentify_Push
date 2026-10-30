"""Required end-to-end test: drives the compiled graph from the trigger to
a terminal state with every dependency faked at the boundary, covering the
happy path (full conversion) plus at least one branch (duplicate refusal and
the two side flows).
"""

from __future__ import annotations

from orchestrator_app.config import Settings
from orchestrator_app.runtime import OrchestratorRuntime

from _fakes import happy_path_trigger_payload, install_fakes


def _runtime() -> OrchestratorRuntime:
    return OrchestratorRuntime(settings=Settings(DRY_RUN=True))


async def test_happy_path_lead_reaches_converted() -> None:
    runtime = _runtime()
    install_fakes(runtime.client)

    run, result = await runtime.start_run("lead", happy_path_trigger_payload())

    assert run.status == "completed"
    assert run.current_node == "end_converted"
    assert result["result"]["outcome"] == "converted"
    assert result["policy"]["policy_number"].startswith("PC-")
    # milestone events fired exactly once each on the happy path
    event_types = [e["event_type"] for e in runtime.events.published]
    assert event_types.count("lead.agent_assigned") == 1
    assert event_types.count("lead.quote_issued") == 1
    assert event_types.count("lead.policy_issued") == 1
    assert event_types.count("flow.lead_intake_started") == 1
    assert "lead.lost" not in event_types


async def test_duplicate_lead_is_refused_without_reaching_assignment() -> None:
    runtime = _runtime()
    install_fakes(runtime.client, {"register_lead": {"lead_id": "lead-dup", "duplicate_found": True}})

    run, result = await runtime.start_run("lead", happy_path_trigger_payload())

    assert run.status == "completed"
    assert run.current_node == "duplicate_declined"
    assert result["lost_reason"] == "Duplicate lead"
    runtime.client.auto_assign_agent.assert_not_awaited()


async def test_reassignment_subflow_reaches_end_reassign() -> None:
    runtime = _runtime()
    install_fakes(runtime.client)

    run, result = await runtime.start_run(
        "reassignment", {"run_type": "reassignment", "reassignment": {"lead_id": "lead-9", "new_agent_id": "agent-2"}}
    )

    assert run.status == "completed"
    assert run.current_node == "end_reassign"
    assert result["result"]["outcome"] == "reassigned"
    runtime.client.reassign_lead.assert_awaited_once_with("lead-9", "agent-2")


async def test_access_report_subflow_reaches_end_access_counts() -> None:
    runtime = _runtime()
    install_fakes(runtime.client)

    run, result = await runtime.start_run(
        "access_report", {"run_type": "access_report", "access_report": {"lead_id": "lead-9", "role": "manager"}}
    )

    assert run.status == "completed"
    assert run.current_node == "end_access_counts"
    assert result["result"]["outcome"] == "access_and_reporting_available"


async def test_agent_management_subflow_calls_the_one_frozen_endpoint() -> None:
    runtime = _runtime()
    install_fakes(runtime.client)

    run, result = await runtime.start_run(
        "agent_management", {"run_type": "agent_management", "agent_record": {"agent_id": "agent-5", "city": "Pune"}}
    )

    assert run.status == "completed"
    assert run.current_node == "end_access_counts"
    runtime.client.upsert_agent_record.assert_awaited_once_with({"agent_id": "agent-5", "city": "Pune"})
