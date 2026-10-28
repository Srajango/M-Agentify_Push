"""Client quote decision and the automatic quote-expiry check — node:
client_decision_wait."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from conftest import register_lead, submit_complete_risk
from lead_domain.config import get_settings
from lead_domain.db import get_database
from lead_domain.models import Quote


def _quoted_lead(client: TestClient, mobile_number: str, vehicle_registration_number: str) -> dict:
    lead = register_lead(
        client, mobile_number=mobile_number, vehicle_registration_number=vehicle_registration_number
    )
    submit_complete_risk(client, lead["lead_id"])
    client.post(f"/leads/{lead['lead_id']}/risk/screen")
    client.post(f"/leads/{lead['lead_id']}/quote")
    return lead


def test_decline_with_valid_reason_sets_lead_lost(client: TestClient) -> None:
    lead = _quoted_lead(client, "9876555001", "MH12RR1111")
    response = client.post(
        f"/leads/{lead['lead_id']}/decision", json={"action": "decline", "reason": "price"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["lead_status"] == "Lost"
    assert body["lost_reason"] == "price"


def test_decline_without_reason_is_rejected(client: TestClient) -> None:
    lead = _quoted_lead(client, "9876555002", "MH12RR2222")
    response = client.post(f"/leads/{lead['lead_id']}/decision", json={"action": "decline"})
    assert response.status_code == 422


def test_accept_reports_current_quote_status(client: TestClient) -> None:
    lead = _quoted_lead(client, "9876555003", "MH12RR3333")
    response = client.post(f"/leads/{lead['lead_id']}/decision", json={"action": "accept"})
    assert response.status_code == 200
    body = response.json()
    assert body["lead_status"] == "Quoted"
    assert body["quote_status"] == "Active"
    assert body["quote_id"]


def test_decision_without_an_active_quote_is_a_conflict(client: TestClient) -> None:
    lead = register_lead(client, mobile_number="9876555004", vehicle_registration_number="MH12RR4444")
    response = client.post(f"/leads/{lead['lead_id']}/decision", json={"action": "accept"})
    assert response.status_code == 409


def test_quote_past_its_seventh_day_automatically_expires_to_lost(client: TestClient) -> None:
    lead = _quoted_lead(client, "9876555005", "MH12RR5555")
    quotes = client.get(f"/leads/{lead['lead_id']}/quotes").json()
    quote_id = quotes[0]["quote_id"]

    settings = get_settings()
    database = get_database(settings)
    session = database.session_factory()
    quote_row = session.get(Quote, quote_id)
    quote_row.expires_at = datetime.utcnow() - timedelta(days=1)
    session.commit()
    session.close()

    response = client.post(f"/leads/{lead['lead_id']}/decision", json={"action": "accept"})
    assert response.status_code == 409

    lead_after = client.get(f"/leads/{lead['lead_id']}").json()
    assert lead_after["status"] == "Lost"
    assert lead_after["lost_reason"] == "Quote expired"
