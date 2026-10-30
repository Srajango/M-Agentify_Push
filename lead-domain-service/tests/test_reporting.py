"""Role-based visibility and agency reporting counts — nodes:
role_based_access_control, compute_counts_conversion."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from conftest import create_agent, register_lead, submit_complete_risk


def test_agent_sees_only_their_own_leads(client: TestClient) -> None:
    agent_a = create_agent(client, name="A", city="Mumbai", active=True)
    agent_b = create_agent(client, name="B", city="Mumbai", active=True)
    lead_a = register_lead(client, mobile_number="9876577001", vehicle_registration_number="MH12TT1111")
    client.post(f"/leads/{lead_a['lead_id']}/assign", params={"manager_agent_id": agent_a["agent_id"]})
    lead_b = register_lead(client, mobile_number="9876577002", vehicle_registration_number="MH12TT2222")
    client.post(f"/leads/{lead_b['lead_id']}/assign", params={"manager_agent_id": agent_b["agent_id"]})

    response = client.get("/leads", params={"role": "agent", "agent_id": agent_a["agent_id"]})
    assert response.status_code == 200
    body = response.json()
    assert {l["lead_id"] for l in body["leads"]} == {lead_a["lead_id"]}


def test_manager_sees_every_lead(client: TestClient) -> None:
    register_lead(client, mobile_number="9876577003", vehicle_registration_number="MH12TT3333")
    register_lead(client, mobile_number="9876577004", vehicle_registration_number="MH12TT4444")
    response = client.get("/leads", params={"role": "manager"})
    assert len(response.json()["leads"]) == 2


def test_underwriter_sees_only_the_referral_queue(client: TestClient) -> None:
    lead_referred = register_lead(
        client, mobile_number="9876577005", vehicle_registration_number="MH12TT5555"
    )
    submit_complete_risk(client, lead_referred["lead_id"], prior_claims_count=3, registration_year=2022)
    client.post(f"/leads/{lead_referred['lead_id']}/risk/screen")

    register_lead(client, mobile_number="9876577006", vehicle_registration_number="MH12TT6666")

    response = client.get("/leads", params={"role": "underwriter"})
    leads = response.json()["leads"]
    assert [l["lead_id"] for l in leads] == [lead_referred["lead_id"]]


def test_agent_role_without_agent_id_is_rejected(client: TestClient) -> None:
    response = client.get("/leads", params={"role": "agent"})
    assert response.status_code == 422


def test_unknown_role_is_forbidden(client: TestClient) -> None:
    response = client.get("/leads", params={"role": "accountant"})
    assert response.status_code == 403


def test_conversion_rate_is_computed_live_from_lead_records(client: TestClient) -> None:
    agent = create_agent(client, city="Mumbai", active=True)
    converted_lead = register_lead(
        client, mobile_number="9876577007", vehicle_registration_number="MH12TT7777"
    )
    client.post(
        f"/leads/{converted_lead['lead_id']}/assign", params={"manager_agent_id": agent["agent_id"]}
    )
    submit_complete_risk(client, converted_lead["lead_id"])
    client.post(f"/leads/{converted_lead['lead_id']}/risk/screen")
    client.post(f"/leads/{converted_lead['lead_id']}/quote")
    quote = client.get(f"/leads/{converted_lead['lead_id']}/quotes").json()[0]
    client.post(
        f"/leads/{converted_lead['lead_id']}/bind",
        json={"effective_date": date.today().isoformat(), "collected_amount": quote["total_premium"]},
    )

    open_lead = register_lead(client, mobile_number="9876577008", vehicle_registration_number="MH12TT8888")
    client.post(f"/leads/{open_lead['lead_id']}/assign", params={"manager_agent_id": agent["agent_id"]})

    response = client.get("/counts")
    assert response.status_code == 200
    body = response.json()
    agent_row = next(a for a in body["agents"] if a["agent_id"] == agent["agent_id"])
    assert agent_row["assigned"] == 2
    assert agent_row["converted"] == 1
    assert agent_row["open"] == 1
    assert agent_row["conversion_rate"] == 0.5

    manager_listing = client.get("/leads", params={"role": "manager"}).json()
    assert manager_listing["counts"]["agency"]["converted"] == 1
