"""Branch coverage beyond the required e2e/gate tests: appetite outcomes,
the risk-capture and re-rate loops, client decision branches, bind
validation failures, and a simulated backend failure that must leave the
run paused at its current node instead of guessing a result.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from orchestrator_app.config import Settings
from orchestrator_app.exceptions import DomainServiceError, ValidationError
from orchestrator_app.runtime import OrchestratorRuntime
from orchestrator_app.state import new_run_state

from _fakes import happy_path_trigger_payload, install_fakes


def _runtime() -> OrchestratorRuntime:
    return OrchestratorRuntime(settings=Settings(DRY_RUN=True))


async def test_appetite_decline_branch_ends_lead_lost() -> None:
    runtime = _runtime()
    install_fakes(runtime.client, {"screen_appetite": {"outcome": "decline"}})

    run, result = await runtime.start_run("lead", happy_path_trigger_payload())

    assert run.current_node == "lead_lost_decline_screen"
    assert result["lost_reason"] == "Declined by screening"
    runtime.client.rate_quote.assert_not_awaited()


async def test_client_decline_branch_records_reason() -> None:
    runtime = _runtime()
    install_fakes(runtime.client, {"fetch_client_decision": {"client_outcome": "decline"}})

    run, result = await runtime.start_run("lead", happy_path_trigger_payload())

    assert run.current_node == "lead_lost_client_decline"
    assert result["lost_reason"] == "Client declined"


async def test_quote_expired_branch() -> None:
    runtime = _runtime()
    install_fakes(runtime.client, {"fetch_client_decision": {"client_outcome": "expired"}})

    run, result = await runtime.start_run("lead", happy_path_trigger_payload())

    assert run.current_node == "lead_lost_quote_expired"
    assert result["lost_reason"] == "Quote expired"


async def test_risk_incomplete_loops_back_to_capture_then_proceeds() -> None:
    runtime = _runtime()
    install_fakes(
        runtime.client,
        {"lookup_risk": [{"complete": False, "missing_fields": ["engine_number"]}, {"complete": True}]},
    )

    run, result = await runtime.start_run("lead", happy_path_trigger_payload())

    assert runtime.client.lookup_risk.await_count == 2
    runtime.client.notify_risk_incomplete.assert_awaited_once()
    assert run.current_node == "end_converted"
    assert result["result"]["outcome"] == "converted"


async def test_rerate_loop_runs_the_requested_number_of_times_then_proceeds() -> None:
    runtime = _runtime()
    install_fakes(runtime.client)
    payload = happy_path_trigger_payload()
    payload["lead"]["rerate_requested_count"] = 1

    run, result = await runtime.start_run("lead", payload)

    assert runtime.client.flag_rerate.await_count == 1
    assert runtime.client.rate_quote.await_count == 2  # rated once, then re-rated once more
    assert run.current_node == "end_converted"


async def test_bind_validation_failure_does_not_reach_end_converted() -> None:
    runtime = _runtime()
    install_fakes(runtime.client)
    payload = happy_path_trigger_payload()
    payload["bind_inputs"]["amount_collected"] = 1.0  # does not match the quote total

    with pytest.raises(ValidationError):
        await runtime.start_run("lead", payload)

    run = next(iter(runtime.runs._runs.values()))
    assert run.status == "failed"
    assert run.current_node != "end_converted"


async def test_simulated_backend_failure_leaves_run_paused_at_the_same_node() -> None:
    runtime = _runtime()
    install_fakes(runtime.client)
    runtime.client.auto_assign_agent = AsyncMock(side_effect=DomainServiceError("lead-domain-service timed out"))

    run = runtime.runs.create("lead")
    payload = happy_path_trigger_payload()
    state = new_run_state(run.run_id, "lead", payload)

    with pytest.raises(DomainServiceError):
        await runtime._advance(run, state)
    assert run.status == "failed"

    register_lead_mock = runtime.client.register_lead
    assert register_lead_mock.await_count == 1  # register_lead already committed by the checkpoint

    # Fix the dependency and resume from the SAME checkpoint -- register_lead
    # must not run again, proving the run stayed paused at auto_assign_agent
    # rather than restarting or guessing an outcome.
    runtime.client.auto_assign_agent = AsyncMock(return_value={"assigned": True, "agent_id": "agent-1"})
    result = await runtime._advance(run, None)

    assert register_lead_mock.await_count == 1
    assert run.status == "completed"
    assert result["current_node"] == "end_converted"
