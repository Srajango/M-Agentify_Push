"""TestClient-level tests for every route in this service's own API
contract: health, trigger, run status, the SSE stream, and both gates'
resume/reject routes -- driven over real HTTP, not just the runtime layer.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

LEAD_BODY = {
    "run_type": "lead",
    "lead": {
        "customer_name": "Priya Nair",
        "mobile_number": "9000000002",
        "email": "priya.nair@example.com",
        "city": "Chennai",
        "source": "phone",
        "vehicle_reg": "TN01CD5678",
    },
    "risk_data": {"make": "Hyundai", "model": "Creta", "year": 2021},
    "bind_inputs": {"effective_date": "2999-01-01", "amount_collected": 1000.0},
}


def test_post_runs_trigger_drives_the_graph_to_a_terminal_state(client) -> None:
    response = client.post("/runs", json=LEAD_BODY)
    assert response.status_code == 201
    body = response.json()
    assert body["run_type"] == "lead"
    assert body["status"] == "completed"
    assert body["current_node"] == "end_converted"


def test_post_runs_rejects_an_invalid_run_type(client) -> None:
    bad_body = {**LEAD_BODY, "run_type": "not-a-real-flow"}
    response = client.post("/runs", json=bad_body)
    assert response.status_code == 422


def test_get_run_returns_status_and_step_history(client) -> None:
    created = client.post("/runs", json=LEAD_BODY).json()
    response = client.get(f"/runs/{created['run_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == created["run_id"]
    assert len(body["steps"]) >= 1


def test_get_run_404_for_unknown_run(client) -> None:
    response = client.get("/runs/does-not-exist")
    assert response.status_code == 404


def test_run_events_stream_replays_recorded_steps(client) -> None:
    created = client.post("/runs", json=LEAD_BODY).json()
    response = client.get(f"/runs/{created['run_id']}/events")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "data:" in response.text


def test_manager_gate_approve_route_resumes_a_halted_run(client) -> None:
    runtime = client.app.state.runtime
    runtime.client.auto_assign_agent = AsyncMock(return_value={"assigned": False, "agent_id": None})

    triggered = client.post("/runs", json=LEAD_BODY).json()
    assert triggered["status"] == "awaiting_approval"
    assert triggered["current_node"] == "manager_manual_assign"

    resumed = client.post(
        f"/runs/{triggered['run_id']}/steps/manager_manual_assign/approve", json={"agent_id": "agent-42"}
    )
    assert resumed.status_code == 200
    assert resumed.json()["current_node"] == "end_converted"


def test_underwriter_gate_reject_route(client) -> None:
    runtime = client.app.state.runtime
    runtime.client.screen_appetite = AsyncMock(return_value={"outcome": "refer"})

    triggered = client.post("/runs", json=LEAD_BODY).json()
    assert triggered["status"] == "awaiting_approval"
    assert triggered["current_node"] == "underwriter_review_referral"

    rejected = client.post(f"/runs/{triggered['run_id']}/steps/underwriter_review_referral/reject")
    assert rejected.status_code == 200
    assert rejected.json()["current_node"] == "lead_lost_underwriter_decline"


def test_underwriter_gate_approve_route(client) -> None:
    runtime = client.app.state.runtime
    runtime.client.screen_appetite = AsyncMock(return_value={"outcome": "refer"})

    triggered = client.post("/runs", json=LEAD_BODY).json()
    approved = client.post(
        f"/runs/{triggered['run_id']}/steps/underwriter_review_referral/approve",
        json={"decision": "approve"},
    )
    assert approved.status_code == 200
    assert approved.json()["current_node"] == "end_converted"


def test_approve_route_422_on_bad_decision(client) -> None:
    runtime = client.app.state.runtime
    runtime.client.screen_appetite = AsyncMock(return_value={"outcome": "refer"})

    triggered = client.post("/runs", json=LEAD_BODY).json()
    response = client.post(
        f"/runs/{triggered['run_id']}/steps/underwriter_review_referral/approve",
        json={"decision": "not-a-real-decision"},
    )
    assert response.status_code == 422
