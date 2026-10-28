"""Inbound workflow events from the gate-owning orchestrator — logged for
audit correlation, never raising on duplicate delivery."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_receiving_a_workflow_event_logs_and_acks(client: TestClient) -> None:
    response = client.post(
        "/webhooks/workflow-events",
        json={
            "event_id": "evt-1",
            "event_type": "underwriter_decision_made",
            "lead_id": "lead-abc",
            "payload": {"decision": "Approved"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "received"
    assert body["duplicate"] is False


def test_duplicate_delivery_is_acknowledged_not_raised(client: TestClient) -> None:
    payload = {
        "event_id": "evt-2",
        "event_type": "client_accepted",
        "lead_id": "lead-xyz",
        "payload": {},
    }
    first = client.post("/webhooks/workflow-events", json=payload)
    second = client.post("/webhooks/workflow-events", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True


def test_unknown_event_type_is_rejected_at_the_boundary(client: TestClient) -> None:
    response = client.post(
        "/webhooks/workflow-events",
        json={"event_id": "evt-3", "event_type": "not_a_real_event", "payload": {}},
    )
    assert response.status_code == 422
