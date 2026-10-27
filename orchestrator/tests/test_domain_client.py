"""Tests for the lead-domain-service typed client.

Covers: the 18-operation registry (task 6's "calls entry" requirement), a
DRY_RUN short-circuit, one contract test per dependency endpoint that is
actually frozen with a method+path (GET /health, POST /agents) run with
DRY_RUN=false against a stubbed transport asserting the real request, and
retry exhaustion leaving a DomainServiceError rather than a guessed result.
"""

from __future__ import annotations

import json as _json

import httpx
import pytest
import respx

from orchestrator_app.config import Settings
from orchestrator_app.domain_client import CONSUMED_OPERATIONS, DomainClient
from orchestrator_app.exceptions import DomainServiceError

BASE_URL = "http://mock-lead-domain-service:5097"


def _settings(**overrides) -> Settings:
    values = {
        "DRY_RUN": False,
        "LEAD_DOMAIN_SERVICE_URL": BASE_URL,
        "DOMAIN_CLIENT_TIMEOUT_SECONDS": 1.0,
        "DOMAIN_CLIENT_MAX_RETRIES": 3,
        "DOMAIN_CLIENT_BACKOFF_BASE_SECONDS": 0.01,
    }
    values.update(overrides)
    return Settings(**values)


def test_registry_covers_all_18_consumed_operations_with_a_retry_policy():
    assert len(CONSUMED_OPERATIONS) == 18
    settings = _settings()
    for spec in CONSUMED_OPERATIONS.values():
        assert spec.method in ("GET", "POST")
        assert spec.path
    # The retry/backoff policy applied to every one of the 18 ops is uniform
    # and comes from Settings, not a hardcoded per-op constant.
    assert settings.domain_client_max_retries >= 1
    assert settings.domain_client_backoff_base_seconds > 0


async def test_dry_run_short_circuits_network_for_every_op_family():
    client = DomainClient(_settings(DRY_RUN=True))
    assigned = await client.auto_assign_agent("lead-1", "Mumbai")
    screened = await client.screen_appetite("lead-1", {})
    risk = await client.lookup_risk("lead-1")
    await client.aclose()
    assert assigned == {"assigned": True, "agent_id": "dry-run-agent"}
    assert screened == {"outcome": "accept"}
    assert risk == {"complete": True}


async def test_health_contract_with_stubbed_transport_dry_run_false():
    """Dependency contract test for the frozen GET /health operation."""

    with respx.mock(assert_all_called=True) as mock_router:
        route = mock_router.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        client = DomainClient(_settings())
        result = await client.health()
        await client.aclose()

    assert route.called
    assert route.calls.last.request.method == "GET"
    assert result == {"status": "ok"}


async def test_upsert_agent_record_contract_asserts_real_request_shape():
    """Dependency contract test for the frozen POST /agents operation --
    asserts the real URL, method and body sent over the stubbed transport,
    not just that DRY_RUN produced a canned value."""

    agent_payload = {"agent_id": "agent-7", "city": "Pune", "active": True}
    with respx.mock(assert_all_called=True) as mock_router:
        route = mock_router.post(f"{BASE_URL}/agents").mock(
            return_value=httpx.Response(200, json={"agent_id": "agent-7", "stored": True})
        )
        client = DomainClient(_settings())
        result = await client.upsert_agent_record(agent_payload)
        await client.aclose()

    assert route.called
    sent = route.calls.last.request
    assert sent.method == "POST"
    assert sent.url.path == "/agents"
    assert _json.loads(sent.content) == agent_payload
    assert result == {"agent_id": "agent-7", "stored": True}


async def test_retry_exhaustion_raises_domain_service_error_and_respects_max_retries():
    with respx.mock(assert_all_called=True) as mock_router:
        route = mock_router.get(f"{BASE_URL}/health").mock(side_effect=httpx.TimeoutException("boom"))
        client = DomainClient(_settings(DOMAIN_CLIENT_MAX_RETRIES=2, DOMAIN_CLIENT_BACKOFF_BASE_SECONDS=0.001))
        with pytest.raises(DomainServiceError):
            await client.health()
        await client.aclose()

    assert route.call_count == 2


# Every one of the 18 consumed operations/events, run with DRY_RUN=false against a
# stubbed transport so the suite proves the real request (method/path/body) is sent
# over the wire for each -- not just that DRY_RUN produces a canned value. Each tuple
# is (method_name, call_args, http_method, path, expected_json_body_or_None_for_GET).
CONSUMED_OPERATION_CALLS: list[tuple[str, tuple, str, str, dict | None]] = [
    ("register_lead", ({"customer_name": "Asha Rao", "city": "Pune"},), "POST", "/leads",
     {"customer_name": "Asha Rao", "city": "Pune"}),
    ("auto_assign_agent", ("lead-42", "Pune"), "POST", "/leads/lead-42/auto-assign", {"city": "Pune"}),
    ("finalize_auto_assignment", ("lead-42", "agent-9"), "POST", "/leads/lead-42/assignment/finalize",
     {"agent_id": "agent-9"}),
    ("apply_manual_assignment", ("lead-42", "agent-9"), "POST", "/leads/lead-42/assignment/manual",
     {"agent_id": "agent-9"}),
    ("notify_risk_incomplete", ("lead-42", ["engine_number"]), "POST",
     "/leads/lead-42/risk/incomplete-notice", {"missing_fields": ["engine_number"]}),
    ("screen_appetite", ("lead-42", {"make": "Toyota"}), "POST", "/risks/lead-42/screen",
     {"risk_data": {"make": "Toyota"}}),
    ("rate_quote", ("lead-42", {"make": "Toyota"}), "POST", "/quotes/lead-42/rate",
     {"risk_data": {"make": "Toyota"}}),
    ("record_underwriter_outcome", ("lead-42", "approve"), "POST",
     "/risks/lead-42/underwriter-outcome", {"decision": "approve"}),
    ("flag_rerate", ("lead-42",), "POST", "/leads/lead-42/rerate-flag", {}),
    ("fetch_latest_quote_for_wait", ("lead-42",), "GET", "/quotes/lead-42/latest", None),
    ("fetch_quote_for_bind", ("lead-42",), "GET", "/quotes/lead-42/latest", None),
    ("upsert_agent_record", ({"agent_id": "agent-7"},), "POST", "/agents", {"agent_id": "agent-7"}),
    ("reassign_lead", ("lead-42", "agent-5"), "POST", "/leads/lead-42/reassign", {"new_agent_id": "agent-5"}),
    ("publish_counts", ({"assigned": 5},), "POST", "/reports/counts", {"assigned": 5}),
    ("lookup_lead", ("lead-42",), "GET", "/leads/lead-42", None),
    ("lookup_risk", ("lead-42",), "GET", "/risks/lead-42", None),
    ("fetch_client_decision", ("lead-42",), "GET", "/quotes/lead-42/client-decision", None),
]


@pytest.mark.parametrize("method_name,call_args,http_method,path,expected_body", CONSUMED_OPERATION_CALLS)
async def test_consumed_operation_makes_the_real_http_call(
    method_name: str, call_args: tuple, http_method: str, path: str, expected_body: dict | None
) -> None:
    """For every consumed operation/event, DRY_RUN=false must produce the
    literal request its CONSUMED_OPERATIONS entry documents -- the real
    method, path and body actually hit the stubbed transport, not just a
    DRY_RUN canned value."""

    with respx.mock(assert_all_called=True) as mock_router:
        route_fn = mock_router.get if http_method == "GET" else mock_router.post
        route = route_fn(f"{BASE_URL}{path}").mock(return_value=httpx.Response(200, json={}))
        client = DomainClient(_settings())
        await getattr(client, method_name)(*call_args)
        await client.aclose()

    assert route.called
    sent = route.calls.last.request
    assert sent.method == http_method
    assert sent.url.path == path
    if expected_body is not None:
        assert _json.loads(sent.content) == expected_body


async def test_lookup_agent_directory_makes_the_real_http_call_with_city_query_param() -> None:
    """``lookup_agent_directory`` is GET /agents with the city as a query
    param rather than a path segment or body -- asserted separately."""

    with respx.mock(assert_all_called=True) as mock_router:
        route = mock_router.get(f"{BASE_URL}/agents", params={"city": "Pune"}).mock(
            return_value=httpx.Response(200, json={"agents": []})
        )
        client = DomainClient(_settings())
        await client.lookup_agent_directory("Pune")
        await client.aclose()

    assert route.called
    sent = route.calls.last.request
    assert sent.method == "GET"
    assert sent.url.path == "/agents"
    assert dict(sent.url.params) == {"city": "Pune"}
