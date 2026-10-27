"""Rate card engine and versioned quoting — node: auto_rate_quote."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import register_lead, submit_complete_risk


def _approve_clear(
    client: TestClient,
    *,
    mobile_number: str,
    vehicle_registration_number: str,
    coverage_type: str,
    idv: str,
    no_claim_bonus_fraction: str,
    prior_claims_count: int,
    registration_year: int,
) -> dict:
    lead = register_lead(
        client, mobile_number=mobile_number, vehicle_registration_number=vehicle_registration_number
    )
    submit_complete_risk(
        client,
        lead["lead_id"],
        coverage_type=coverage_type,
        idv=idv,
        no_claim_bonus_fraction=no_claim_bonus_fraction,
        prior_claims_count=prior_claims_count,
        registration_year=registration_year,
    )
    client.post(f"/leads/{lead['lead_id']}/risk/screen")
    return lead


def test_comprehensive_rating_formula_and_rounding(client: TestClient) -> None:
    lead = _approve_clear(
        client,
        mobile_number="9876511111",
        vehicle_registration_number="MH12QQ1111",
        coverage_type="Comprehensive",
        idv="300000.00",
        no_claim_bonus_fraction="0.20",
        prior_claims_count=0,
        registration_year=2022,
    )
    response = client.post(f"/leads/{lead['lead_id']}/quote")
    assert response.status_code == 200
    body = response.json()
    # own damage = 300000 * 0.035 * (1 - 0.20) = 8400.00
    assert float(body["own_damage_premium"]) == 8400.0
    assert float(body["third_party_premium"]) == 2072.0
    # total = 8400 + 2072 = 10472, no loading, rounded to nearest rupee
    assert body["total_premium"] == 10472
    assert body["version"] == 1
    assert body["status"] == "Active"
    assert body["lead_status"] == "Quoted"


def test_third_party_rating_has_no_own_damage_component(client: TestClient) -> None:
    lead = _approve_clear(
        client,
        mobile_number="9876522222",
        vehicle_registration_number="MH12QQ2222",
        coverage_type="ThirdParty",
        idv="300000.00",
        no_claim_bonus_fraction="0.20",
        prior_claims_count=0,
        registration_year=2022,
    )
    response = client.post(f"/leads/{lead['lead_id']}/quote")
    body = response.json()
    assert float(body["own_damage_premium"]) == 0.0
    assert body["total_premium"] == 2072


def test_rerating_creates_new_version_and_replaces_previous(client: TestClient) -> None:
    lead = _approve_clear(
        client,
        mobile_number="9876533333",
        vehicle_registration_number="MH12QQ3333",
        coverage_type="Comprehensive",
        idv="300000.00",
        no_claim_bonus_fraction="0.20",
        prior_claims_count=0,
        registration_year=2022,
    )
    first = client.post(f"/leads/{lead['lead_id']}/quote").json()
    second = client.post(f"/leads/{lead['lead_id']}/quote").json()

    assert second["version"] == first["version"] + 1
    quotes = client.get(f"/leads/{lead['lead_id']}/quotes").json()
    by_version = {q["version"]: q for q in quotes}
    assert by_version[first["version"]]["status"] == "Replaced"
    assert by_version[second["version"]]["status"] == "Active"


def test_rating_without_an_approved_risk_is_rejected(client: TestClient) -> None:
    lead = register_lead(client, mobile_number="9876544444", vehicle_registration_number="MH12QQ4444")
    response = client.post(f"/leads/{lead['lead_id']}/quote")
    assert response.status_code == 409
