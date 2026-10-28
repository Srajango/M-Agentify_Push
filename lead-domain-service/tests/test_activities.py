"""Agent contact activities — node: record_contact_activity."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import create_agent, register_lead


def test_record_contact_activity_appends_row(client: TestClient) -> None:
    agent = create_agent(client)
    lead = register_lead(client)
    response = client.post(
        f"/leads/{lead['lead_id']}/activities",
        json={
            "agent_id": agent["agent_id"],
            "channel": "whatsapp",
            "outcome": "follow_up_booked",
            "note": "Will call back tomorrow",
            "next_follow_up_date": "2026-11-01",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["channel"] == "whatsapp"
    assert body["next_follow_up_date"] == "2026-11-01"

    activities = client.get(f"/leads/{lead['lead_id']}/activities").json()
    assert len(activities) == 1


def test_recording_multiple_activities_only_ever_appends(client: TestClient) -> None:
    agent = create_agent(client)
    lead = register_lead(client)
    for outcome in ("no_answer", "interested"):
        client.post(
            f"/leads/{lead['lead_id']}/activities",
            json={
                "agent_id": agent["agent_id"],
                "channel": "call",
                "outcome": outcome,
                "note": f"attempt: {outcome}",
            },
        )
    activities = client.get(f"/leads/{lead['lead_id']}/activities").json()
    assert len(activities) == 2
    assert [a["outcome"] for a in activities] == ["no_answer", "interested"]


def test_no_route_exists_to_edit_or_delete_an_activity(client: TestClient) -> None:
    agent = create_agent(client)
    lead = register_lead(client)
    client.post(
        f"/leads/{lead['lead_id']}/activities",
        json={"agent_id": agent["agent_id"], "channel": "call", "outcome": "no_answer", "note": "n/a"},
    )

    # The only routes on this path are GET (list) and POST (append); there
    # is no update or delete method registered for it anywhere in the app.
    assert client.put(f"/leads/{lead['lead_id']}/activities").status_code == 405
    assert client.delete(f"/leads/{lead['lead_id']}/activities").status_code == 405


def test_activity_for_unknown_agent_returns_404(client: TestClient) -> None:
    lead = register_lead(client)
    response = client.post(
        f"/leads/{lead['lead_id']}/activities",
        json={"agent_id": "does-not-exist", "channel": "call", "outcome": "no_answer", "note": "n/a"},
    )
    assert response.status_code == 404
