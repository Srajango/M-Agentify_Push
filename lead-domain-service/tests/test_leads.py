"""Lead registration, duplicate blocking, round-robin/manual assignment and
manager reassignment — nodes: register_lead, auto_assign_agent,
manager_reassign_lead."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import create_agent, register_lead, submit_complete_risk


def test_register_lead_happy_path(client: TestClient) -> None:
    lead = register_lead(client)
    assert lead["status"] == "New"
    assert lead["product"] == "Private Car"


def test_register_lead_missing_field_returns_422(client: TestClient) -> None:
    response = client.post(
        "/leads",
        json={
            "customer_name": "Ravi",
            "mobile_number": "9876500001",
            "city": "Mumbai",
            "source": "website",
            "vehicle_registration_number": "MH12AB1234",
        },
    )
    assert response.status_code == 422


def test_duplicate_open_lead_is_refused(client: TestClient) -> None:
    register_lead(client, mobile_number="9876500002", vehicle_registration_number="MH12ZZ9999")
    response = client.post(
        "/leads",
        json={
            "customer_name": "Someone Else",
            "mobile_number": "9876500002",
            "email": "someone@example.com",
            "city": "Mumbai",
            "source": "referral",
            "vehicle_registration_number": "MH12ZZ9999",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_lead"

    listing = client.get("/leads", params={"role": "manager"}).json()
    matching = [
        l
        for l in listing["leads"]
        if l["mobile_number"] == "9876500002" and l["vehicle_registration_number"] == "MH12ZZ9999"
    ]
    assert len(matching) == 1


def test_registering_a_new_combination_succeeds(client: TestClient) -> None:
    register_lead(client, mobile_number="9876500003", vehicle_registration_number="MH12AA1111")
    response = register_lead(
        client, mobile_number="9876500003", vehicle_registration_number="MH12AA2222"
    )
    assert response["status"] == "New"


def test_auto_assignment_never_leaves_lead_unassigned_when_agent_active(client: TestClient) -> None:
    agent = create_agent(client, city="Mumbai", active=True)
    lead = register_lead(client, city="Mumbai")
    assert lead["agent_id"] == agent["agent_id"]


def test_lead_stays_unassigned_with_no_active_agent_in_city(client: TestClient) -> None:
    lead = register_lead(client, city="Nowhereville", mobile_number="9876500004")
    assert lead["agent_id"] is None


def test_reassigning_converted_or_lost_lead_is_rejected(client: TestClient) -> None:
    agent_a = create_agent(client, name="A", city="Mumbai", active=True)
    agent_b = create_agent(client, name="B", city="Mumbai", active=True)
    lead = register_lead(client, mobile_number="9876500005", vehicle_registration_number="MH12BB1111")
    client.post(f"/leads/{lead['lead_id']}/assign", params={"manager_agent_id": agent_a["agent_id"]})

    submit_complete_risk(client, lead["lead_id"], registration_year=2005)
    screen = client.post(f"/leads/{lead['lead_id']}/risk/screen")
    assert screen.json()["lead_status"] == "Lost"

    response = client.post(
        f"/leads/{lead['lead_id']}/reassign", json={"new_agent_id": agent_b["agent_id"]}
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_reassign_open_lead_keeps_status_and_activities(client: TestClient) -> None:
    agent_a = create_agent(client, name="A", city="Mumbai", active=True)
    agent_b = create_agent(client, name="B", city="Mumbai", active=True)
    lead = register_lead(client, mobile_number="9876500006", vehicle_registration_number="MH12CC1111")
    client.post(f"/leads/{lead['lead_id']}/assign", params={"manager_agent_id": agent_a["agent_id"]})
    client.post(
        f"/leads/{lead['lead_id']}/activities",
        json={
            "agent_id": agent_a["agent_id"],
            "channel": "call",
            "outcome": "interested",
            "note": "Discussed the policy options",
        },
    )

    response = client.post(
        f"/leads/{lead['lead_id']}/reassign", json={"new_agent_id": agent_b["agent_id"]}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["agent_id"] == agent_b["agent_id"]
    assert body["status"] == "New"

    activities = client.get(f"/leads/{lead['lead_id']}/activities").json()
    assert len(activities) == 1


def test_reassign_to_inactive_agent_is_rejected(client: TestClient) -> None:
    agent_a = create_agent(client, name="A", city="Mumbai", active=True)
    inactive_agent = create_agent(client, name="C", city="Mumbai", active=False)
    lead = register_lead(client, mobile_number="9876500007", vehicle_registration_number="MH12DD1111")
    client.post(f"/leads/{lead['lead_id']}/assign", params={"manager_agent_id": agent_a["agent_id"]})

    response = client.post(
        f"/leads/{lead['lead_id']}/reassign", json={"new_agent_id": inactive_agent["agent_id"]}
    )
    assert response.status_code == 422


def test_reassign_nonexistent_lead_returns_404(client: TestClient) -> None:
    agent = create_agent(client, city="Mumbai", active=True)
    response = client.post(
        "/leads/does-not-exist/reassign", json={"new_agent_id": agent["agent_id"]}
    )
    assert response.status_code == 404
