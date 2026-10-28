"""POST /agents — frozen contract op_9fcce42948fc43c0."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import create_agent


def test_create_agent_happy_path(client: TestClient) -> None:
    response = client.post("/agents", json={"name": "Priya Nair", "city": "Pune", "active": True})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Priya Nair"
    assert body["city"] == "Pune"
    assert body["active"] is True
    assert body["agent_id"]


def test_update_agent_by_id(client: TestClient) -> None:
    agent = create_agent(client, name="Priya Nair", city="Pune", active=True)
    response = client.post(
        "/agents",
        json={"agent_id": agent["agent_id"], "name": "Priya Nair", "city": "Pune", "active": False},
    )
    assert response.status_code == 200
    assert response.json()["active"] is False


def test_update_unknown_agent_returns_404(client: TestClient) -> None:
    response = client.post(
        "/agents", json={"agent_id": "does-not-exist", "name": "X", "city": "Pune", "active": True}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_create_agent_missing_field_returns_422(client: TestClient) -> None:
    response = client.post("/agents", json={"city": "Pune", "active": True})
    assert response.status_code == 422


def test_deactivating_agent_removes_from_active_roster(client: TestClient) -> None:
    agent = create_agent(client, city="Pune", active=True)
    response = client.get("/agents", params={"city": "Pune", "active": True})
    assert any(a["agent_id"] == agent["agent_id"] for a in response.json())

    client.post(
        "/agents",
        json={"agent_id": agent["agent_id"], "name": agent["name"], "city": "Pune", "active": False},
    )
    response = client.get("/agents", params={"city": "Pune", "active": True})
    assert all(a["agent_id"] != agent["agent_id"] for a in response.json())
