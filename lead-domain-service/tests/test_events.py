"""Domain event publishing — DRY_RUN switches only the outbound transport.
Each of the four events (lead-registered, lead-status-changed,
quote-issued, policy-issued) gets a dedicated test for its exact trigger
point, plus one test exercising the real DRY_RUN=false HTTP path."""

from __future__ import annotations

import json

import httpx
import respx
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from conftest import register_lead, submit_complete_risk
from lead_domain.config import get_settings
from lead_domain.events import EventPublisher


def test_lead_registered_event_published_exactly_once(client: TestClient, mocker: MockerFixture) -> None:
    calls: list[str] = []
    original = EventPublisher.publish

    def spy(self: EventPublisher, event_type: str, payload: dict) -> dict:
        calls.append(event_type)
        return original(self, event_type, payload)

    mocker.patch.object(EventPublisher, "publish", spy)

    register_lead(client, mobile_number="9876588001", vehicle_registration_number="MH12UU1111")
    assert calls.count("lead-registered") == 1


def test_lead_status_changed_event_published_exactly_once_on_capture(
    client: TestClient, mocker: MockerFixture
) -> None:
    calls: list[str] = []
    original = EventPublisher.publish

    def spy(self: EventPublisher, event_type: str, payload: dict) -> dict:
        calls.append(event_type)
        return original(self, event_type, payload)

    mocker.patch.object(EventPublisher, "publish", spy)

    lead = register_lead(client, mobile_number="9876588002", vehicle_registration_number="MH12UU2222")
    calls.clear()
    submit_complete_risk(client, lead["lead_id"])
    assert calls.count("lead-status-changed") == 1


def test_quote_issued_event_published_exactly_once(client: TestClient, mocker: MockerFixture) -> None:
    calls: list[str] = []
    original = EventPublisher.publish

    def spy(self: EventPublisher, event_type: str, payload: dict) -> dict:
        calls.append(event_type)
        return original(self, event_type, payload)

    mocker.patch.object(EventPublisher, "publish", spy)

    lead = register_lead(client, mobile_number="9876588003", vehicle_registration_number="MH12UU3333")
    submit_complete_risk(client, lead["lead_id"])
    client.post(f"/leads/{lead['lead_id']}/risk/screen")
    calls.clear()
    client.post(f"/leads/{lead['lead_id']}/quote")
    assert calls.count("quote-issued") == 1


def test_policy_issued_event_published_exactly_once(client: TestClient, mocker: MockerFixture) -> None:
    from datetime import date

    calls: list[str] = []
    original = EventPublisher.publish

    def spy(self: EventPublisher, event_type: str, payload: dict) -> dict:
        calls.append(event_type)
        return original(self, event_type, payload)

    mocker.patch.object(EventPublisher, "publish", spy)

    lead = register_lead(client, mobile_number="9876588004", vehicle_registration_number="MH12UU4444")
    submit_complete_risk(client, lead["lead_id"])
    client.post(f"/leads/{lead['lead_id']}/risk/screen")
    quote = client.post(f"/leads/{lead['lead_id']}/quote").json()
    calls.clear()
    client.post(
        f"/leads/{lead['lead_id']}/bind",
        json={"effective_date": date.today().isoformat(), "collected_amount": quote["total_premium"]},
    )
    assert calls.count("policy-issued") == 1


def test_publish_sends_real_http_request_when_dry_run_false(monkeypatch) -> None:
    """DRY_RUN switches exactly one seam: with it off, publish must perform
    a real httpx POST to ORCHESTRATOR_EVENTS_URL with the event envelope."""

    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("ORCHESTRATOR_EVENTS_URL", "http://orchestrator.test/events")
    settings = get_settings()
    publisher = EventPublisher(settings)

    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.post("http://orchestrator.test/events").mock(
            return_value=httpx.Response(200, json={"status": "accepted"})
        )
        result = publisher.lead_registered("lead-123", "New")

    assert route.called
    request = route.calls.last.request
    assert request.method == "POST"
    body = json.loads(request.content)
    assert body["event_type"] == "lead-registered"
    assert body["payload"] == {"lead_id": "lead-123", "status": "New"}
    assert result == {"status": "accepted"}
