"""Bind validation and policy issuance — nodes: validate_bind_inputs,
bind_and_issue_policy."""

from __future__ import annotations

import re
from datetime import date, timedelta

from fastapi.testclient import TestClient

from conftest import register_lead, submit_complete_risk


def _quoted_lead(client: TestClient, mobile_number: str, vehicle_registration_number: str) -> dict:
    lead = register_lead(
        client, mobile_number=mobile_number, vehicle_registration_number=vehicle_registration_number
    )
    submit_complete_risk(client, lead["lead_id"])
    client.post(f"/leads/{lead['lead_id']}/risk/screen")
    quote = client.post(f"/leads/{lead['lead_id']}/quote").json()
    return {**lead, "quote": quote}


def test_bind_before_today_is_rejected(client: TestClient) -> None:
    lead = _quoted_lead(client, "9876566001", "MH12SS1111")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    response = client.post(
        f"/leads/{lead['lead_id']}/bind",
        json={"effective_date": yesterday, "collected_amount": lead["quote"]["total_premium"]},
    )
    assert response.status_code == 422
    lead_after = client.get(f"/leads/{lead['lead_id']}").json()
    assert lead_after["status"] == "Quoted"


def test_bind_after_quote_expiry_is_rejected(client: TestClient) -> None:
    lead = _quoted_lead(client, "9876566002", "MH12SS2222")
    too_late = (date.today() + timedelta(days=30)).isoformat()
    response = client.post(
        f"/leads/{lead['lead_id']}/bind",
        json={"effective_date": too_late, "collected_amount": lead["quote"]["total_premium"]},
    )
    assert response.status_code == 422


def test_bind_with_wrong_amount_is_rejected(client: TestClient) -> None:
    lead = _quoted_lead(client, "9876566003", "MH12SS3333")
    today = date.today().isoformat()
    response = client.post(
        f"/leads/{lead['lead_id']}/bind",
        json={"effective_date": today, "collected_amount": "1.00"},
    )
    assert response.status_code == 422

    lead_after = client.get(f"/leads/{lead['lead_id']}").json()
    assert lead_after["status"] == "Quoted"


def test_bind_with_valid_inputs_issues_policy_and_converts_lead(client: TestClient) -> None:
    lead = _quoted_lead(client, "9876566004", "MH12SS4444")
    today = date.today().isoformat()
    response = client.post(
        f"/leads/{lead['lead_id']}/bind",
        json={"effective_date": today, "collected_amount": lead["quote"]["total_premium"]},
    )
    assert response.status_code == 201
    body = response.json()
    assert re.fullmatch(r"PC-\d{4}-\d{6}", body["policy_number"])
    assert body["lead_status"] == "Converted"
    assert body["coverage_type"] == lead["quote"]["coverage_type"]
    assert body["effective_date"] == today
    assert "total_premium" in body["premium_breakdown"]

    lead_after = client.get(f"/leads/{lead['lead_id']}").json()
    assert lead_after["status"] == "Converted"


def test_second_bind_on_same_lead_is_rejected(client: TestClient) -> None:
    lead = _quoted_lead(client, "9876566005", "MH12SS5555")
    today = date.today().isoformat()
    first = client.post(
        f"/leads/{lead['lead_id']}/bind",
        json={"effective_date": today, "collected_amount": lead["quote"]["total_premium"]},
    )
    assert first.status_code == 201

    second = client.post(
        f"/leads/{lead['lead_id']}/bind",
        json={"effective_date": today, "collected_amount": lead["quote"]["total_premium"]},
    )
    assert second.status_code == 409
