"""Human-gate tests: the run must HALT at each gate (no downstream call or
state change until resumed), then resume/reject correctly, and resuming or
rejecting twice must be a no-op (idempotent), never a double transition.
"""

from __future__ import annotations

import pytest

from orchestrator_app.config import Settings
from orchestrator_app.exceptions import GateNotAwaitingApprovalError
from orchestrator_app.runtime import OrchestratorRuntime

from _fakes import happy_path_trigger_payload, install_fakes


def _runtime() -> OrchestratorRuntime:
    return OrchestratorRuntime(settings=Settings(DRY_RUN=True))


async def test_manager_gate_halts_then_resumes_exactly_once() -> None:
    runtime = _runtime()
    install_fakes(runtime.client, {"auto_assign_agent": {"assigned": False, "agent_id": None}})

    run, _ = await runtime.start_run("lead", happy_path_trigger_payload())

    # HALT: run paused at the gate, downstream work has not happened.
    assert run.status == "awaiting_approval"
    assert run.current_node == "manager_manual_assign"
    runtime.client.apply_manual_assignment.assert_not_awaited()
    runtime.client.lookup_risk.assert_not_awaited()

    result = await runtime.approve_manager_assignment(run.run_id, "agent-99")

    runtime.client.apply_manual_assignment.assert_awaited_once_with("lead-123", "agent-99")
    assert run.status == "completed"
    assert run.current_node == "end_converted"
    assert result["assigned_agent_id"] == "agent-99"

    # Idempotent: resuming an already-resumed gate is a no-op, not a second assignment.
    noop = await runtime.approve_manager_assignment(run.run_id, "agent-100")
    runtime.client.apply_manual_assignment.assert_awaited_once()  # still exactly one call
    assert noop["current_node"] == "end_converted"


def test_manager_gate_has_no_reject_operation_in_the_frozen_contract(client) -> None:
    """human_gates[manager_manual_assign] names a resume_op_id only -- no
    reject_op_id -- so this service exposes no reject route for it. Verified
    by actually calling the ASGI app rather than introspecting route objects
    (whose concrete type varies across Starlette/FastAPI versions)."""

    response = client.post("/runs/some-run-id/steps/manager_manual_assign/reject")
    assert response.status_code == 404


async def test_underwriter_gate_halts_then_approve_with_loading_resumes() -> None:
    runtime = _runtime()
    install_fakes(runtime.client, {"screen_appetite": {"outcome": "refer"}})

    run, _ = await runtime.start_run("lead", happy_path_trigger_payload())

    assert run.status == "awaiting_approval"
    assert run.current_node == "underwriter_review_referral"
    runtime.client.record_underwriter_outcome.assert_not_awaited()
    runtime.client.rate_quote.assert_not_awaited()

    result = await runtime.approve_underwriter_referral(run.run_id, "approve_with_loading")

    runtime.client.record_underwriter_outcome.assert_awaited_once_with("lead-123", "approve_with_loading")
    assert run.status == "completed"
    assert run.current_node == "end_converted"
    assert result["result"]["outcome"] == "converted"


async def test_underwriter_gate_reject_lands_on_lead_lost_not_the_happy_path() -> None:
    runtime = _runtime()
    install_fakes(runtime.client, {"screen_appetite": {"outcome": "refer"}})

    run, _ = await runtime.start_run("lead", happy_path_trigger_payload())
    assert run.current_node == "underwriter_review_referral"

    result = await runtime.reject_underwriter_referral(run.run_id)

    assert run.current_node == "lead_lost_underwriter_decline"
    assert run.status == "completed"
    assert result["lost_reason"] == "Underwriter declined"
    runtime.client.record_underwriter_outcome.assert_not_awaited()
    runtime.client.rate_quote.assert_not_awaited()
    lost_events = [e for e in runtime.events.published if e["event_type"] == "lead.lost"]
    assert len(lost_events) == 1

    # Idempotent reject: rejecting twice must not fire a second lead.lost event.
    await runtime.reject_underwriter_referral(run.run_id)
    lost_events = [e for e in runtime.events.published if e["event_type"] == "lead.lost"]
    assert len(lost_events) == 1


async def test_resuming_a_gate_the_run_is_not_awaiting_raises() -> None:
    runtime = _runtime()
    install_fakes(runtime.client)  # agent available in city -> gate never reached

    run, _ = await runtime.start_run("lead", happy_path_trigger_payload())
    assert run.current_node != "manager_manual_assign"

    with pytest.raises(GateNotAwaitingApprovalError):
        await runtime.approve_manager_assignment(run.run_id, "agent-1")
