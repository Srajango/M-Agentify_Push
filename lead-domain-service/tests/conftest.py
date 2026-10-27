"""Shared pytest fixtures. DRY_RUN is set per-test (never at module scope or
in an autouse fixture) so each test controls its own transport seam."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from lead_domain.db import reset_database
from lead_domain.events import reset_seen_events
from lead_domain.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """A TestClient against a fresh in-memory database, with DRY_RUN=true
    (the default for most tests) so no outbound HTTP call is attempted."""

    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("DATABASE_URL", "")
    reset_database()
    reset_seen_events()
    with TestClient(app) as test_client:
        yield test_client
    reset_database()


def create_agent(client: TestClient, *, name: str = "Asha Rao", city: str = "Mumbai", active: bool = True) -> dict:
    response = client.post("/agents", json={"name": name, "city": city, "active": active})
    assert response.status_code == 200, response.text
    return response.json()


def register_lead(
    client: TestClient,
    *,
    mobile_number: str = "9876500001",
    vehicle_registration_number: str = "MH12AB1234",
    city: str = "Mumbai",
) -> dict:
    response = client.post(
        "/leads",
        json={
            "customer_name": "Ravi Kumar",
            "mobile_number": mobile_number,
            "email": "ravi.kumar@example.com",
            "city": city,
            "source": "website",
            "vehicle_registration_number": vehicle_registration_number,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def submit_complete_risk(
    client: TestClient,
    lead_id: str,
    *,
    coverage_type: str = "Comprehensive",
    idv: str = "300000.00",
    no_claim_bonus_fraction: str = "0.20",
    prior_claims_count: int = 0,
    registration_year: int = 2022,
) -> dict:
    response = client.post(
        f"/leads/{lead_id}/risk",
        json={
            "vehicle_make": "Maruti",
            "vehicle_model": "Swift",
            "registration_year": registration_year,
            "idv": idv,
            "coverage_type": coverage_type,
            "no_claim_bonus_fraction": no_claim_bonus_fraction,
            "prior_claims_count": prior_claims_count,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()
