"""Risk capture, appetite screening and underwriting outcome — nodes:
capture_risk_data, auto_screen_appetite, record_underwriter_outcome."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import register_lead, submit_complete_risk


def test_incomplete_risk_keeps_lead_in_capture_and_lists_missing_fields(client: TestClient) -> None:
    lead = register_lead(client)
    response = client.post(
        f"/leads/{lead['lead_id']}/risk",
        json={"vehicle_make": "Maruti", "vehicle_model": "Swift"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_complete"] is False
    assert body["lead_status"] == "Capture"
    assert "idv" in body["missing_fields"]
    assert "coverage_type" in body["missing_fields"]


def test_submitting_complete_data_marks_risk_complete(client: TestClient) -> None:
    lead = register_lead(client)
    body = submit_complete_risk(client, lead["lead_id"])
    assert body["is_complete"] is True
    assert body["missing_fields"] == []


def test_risk_submission_for_unknown_lead_returns_404(client: TestClient) -> None:
    response = client.post(
        "/leads/does-not-exist/risk",
        json={"vehicle_make": "Maruti"},
    )
    assert response.status_code == 404


def test_screening_cannot_run_before_risk_is_complete(client: TestClient) -> None:
    lead = register_lead(client)
    response = client.post(f"/leads/{lead['lead_id']}/risk/screen")
    assert response.status_code == 422


def test_decline_rule_sets_lead_lost_and_stops_at_first_match(client: TestClient) -> None:
    lead = register_lead(client)
    submit_complete_risk(client, lead["lead_id"], registration_year=2000, prior_claims_count=10)
    response = client.post(f"/leads/{lead['lead_id']}/risk/screen")
    assert response.status_code == 200
    body = response.json()
    assert body["appetite_outcome"] == "Decline"
    assert body["decline_reason"] == "Vehicle is older than 15 years"
    assert body["lead_status"] == "Lost"


def test_refer_rule_marks_referred_without_changing_status_to_lost(client: TestClient) -> None:
    lead = register_lead(client)
    submit_complete_risk(client, lead["lead_id"], prior_claims_count=3, registration_year=2022)
    response = client.post(f"/leads/{lead['lead_id']}/risk/screen")
    assert response.status_code == 200
    body = response.json()
    assert body["appetite_outcome"] == "Refer"
    assert body["lead_status"] == "Referred"


def test_underwriter_decline_sets_lead_lost_with_reason(client: TestClient) -> None:
    lead = register_lead(client)
    submit_complete_risk(client, lead["lead_id"], prior_claims_count=3, registration_year=2022)
    client.post(f"/leads/{lead['lead_id']}/risk/screen")

    response = client.post(f"/leads/{lead['lead_id']}/risk/underwriting", json={"outcome": "Declined"})
    assert response.status_code == 200
    body = response.json()
    assert body["lead_status"] == "Lost"
    assert body["decline_reason"] == "Underwriter declined"


def test_underwriter_approve_with_loading_stores_latest_approved_risk_and_rates(
    client: TestClient,
) -> None:
    lead = register_lead(client)
    submit_complete_risk(client, lead["lead_id"], prior_claims_count=3, registration_year=2022)
    client.post(f"/leads/{lead['lead_id']}/risk/screen")

    response = client.post(
        f"/leads/{lead['lead_id']}/risk/underwriting",
        json={"outcome": "ApprovedWithLoading", "loading_percent": "10"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_approved"] is True
    assert body["lead_status"] == "Quoted"

    quotes = client.get(f"/leads/{lead['lead_id']}/quotes").json()
    assert len(quotes) == 1
    assert quotes[0]["total_premium"] == 11519


def test_underwriter_outcome_rejected_when_not_referred(client: TestClient) -> None:
    lead = register_lead(client)
    submit_complete_risk(client, lead["lead_id"])
    client.post(f"/leads/{lead['lead_id']}/risk/screen")  # clear, not referred

    response = client.post(f"/leads/{lead['lead_id']}/risk/underwriting", json={"outcome": "Approved"})
    assert response.status_code == 409
