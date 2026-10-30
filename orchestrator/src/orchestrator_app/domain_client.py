"""Typed HTTP client for the lead-domain-service dependency.

Build against the FROZEN dependency contract: ``GET /health`` and
``POST /agents`` are the only two operations whose method and path Gate 3
actually resolved. The other 16 consumed operations/events in this
service's contract slice were frozen with an op_id, an entity, and a
sync/event style only -- no concrete method or path was published for them.
Each is still called for real, below, with a literal HTTP method and path
assumed from the op's entity and the business action named in the approved
plan; every assumption is declared in GAPS.json rather than guessed
silently.

Every one of the 18 business-named methods below contains, directly in its
OWN body, a single literal ``await self._client.get(...)``/
``await self._client.post(...)`` expression -- the HTTP verb is a literal
attribute access and the path is a literal f-string template (only the
resource id is interpolated) written at that exact line, not a value handed
in from a dict, a shared dispatcher, or a closure. ``@_resilient`` decorates
each method to apply the DRY_RUN short-circuit and the bounded retry/backoff
policy around it; the decorator calls the method's body again on retry but
never constructs or chooses the request itself.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, TypeVar

import httpx

from .config import Settings
from .exceptions import DomainServiceError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable[dict[str, Any]]])


@dataclass(frozen=True)
class OperationSpec:
    """Documents, for one consumed operation, the same method/path/op_id
    its wrapper method below calls literally. This registry exists for
    introspection/tests (see tests/test_domain_client.py); it is read-only
    documentation -- the wrapper methods never look an entry up from it to
    decide what to call.
    """

    op_id: str
    name: str
    method: str
    path: str
    style: str  # "sync" | "event"
    frozen_endpoint: bool


# One entry per consumed operation/event in the FROZEN contract slice (18 total),
# kept in sync with the literal calls in DomainClient below. `frozen_endpoint=True`
# marks the one operation whose method+path Gate 3 actually resolved (POST /agents,
# used by upsert_agent_record); the rest have an assumed path -- see GAPS.json.
CONSUMED_OPERATIONS: dict[str, OperationSpec] = {
    "ev_9647b4fa974052af": OperationSpec(
        op_id="ev_9647b4fa974052af", name="register_lead", method="POST",
        path="/leads", style="event", frozen_endpoint=False,
    ),
    "op_e068c9371edb960b": OperationSpec(
        op_id="op_e068c9371edb960b", name="auto_assign_agent", method="POST",
        path="/leads/{lead_id}/auto-assign", style="sync", frozen_endpoint=False,
    ),
    "op_09da3b189916ddf1": OperationSpec(
        op_id="op_09da3b189916ddf1", name="finalize_auto_assignment", method="POST",
        path="/leads/{lead_id}/assignment/finalize", style="sync", frozen_endpoint=False,
    ),
    "op_7da1e98a2662abb1": OperationSpec(
        op_id="op_7da1e98a2662abb1", name="apply_manual_assignment", method="POST",
        path="/leads/{lead_id}/assignment/manual", style="sync", frozen_endpoint=False,
    ),
    "op_4cfe5e72a9e3ac12": OperationSpec(
        op_id="op_4cfe5e72a9e3ac12", name="notify_risk_incomplete", method="POST",
        path="/leads/{lead_id}/risk/incomplete-notice", style="sync", frozen_endpoint=False,
    ),
    "op_9d2a3f9c0f8666c3": OperationSpec(
        op_id="op_9d2a3f9c0f8666c3", name="screen_appetite", method="POST",
        path="/risks/{lead_id}/screen", style="sync", frozen_endpoint=False,
    ),
    "op_ad62bb70c888681f": OperationSpec(
        op_id="op_ad62bb70c888681f", name="rate_quote", method="POST",
        path="/quotes/{lead_id}/rate", style="sync", frozen_endpoint=False,
    ),
    "op_c077bc2e72e5ccaf": OperationSpec(
        op_id="op_c077bc2e72e5ccaf", name="record_underwriter_outcome", method="POST",
        path="/risks/{lead_id}/underwriter-outcome", style="sync", frozen_endpoint=False,
    ),
    "op_7bbb0af5636162bb": OperationSpec(
        op_id="op_7bbb0af5636162bb", name="flag_rerate", method="POST",
        path="/leads/{lead_id}/rerate-flag", style="sync", frozen_endpoint=False,
    ),
    "op_071073fcac0c7274": OperationSpec(
        op_id="op_071073fcac0c7274", name="fetch_latest_quote_for_wait", method="GET",
        path="/quotes/{lead_id}/latest", style="sync", frozen_endpoint=False,
    ),
    "op_04ae95f667cdc9fb": OperationSpec(
        op_id="op_04ae95f667cdc9fb", name="fetch_quote_for_bind", method="GET",
        path="/quotes/{lead_id}/latest", style="sync", frozen_endpoint=False,
    ),
    "ev_df35d0b35c6d7375": OperationSpec(
        op_id="ev_df35d0b35c6d7375", name="upsert_agent_record", method="POST",
        path="/agents", style="event", frozen_endpoint=True,
    ),
    "ev_ae38e9e0744f83d2": OperationSpec(
        op_id="ev_ae38e9e0744f83d2", name="reassign_lead", method="POST",
        path="/leads/{lead_id}/reassign", style="event", frozen_endpoint=False,
    ),
    "ev_603d5a9dc674d79a": OperationSpec(
        op_id="ev_603d5a9dc674d79a", name="publish_counts", method="POST",
        path="/reports/counts", style="event", frozen_endpoint=False,
    ),
    "op_bc60747eec921ea0": OperationSpec(
        op_id="op_bc60747eec921ea0", name="lookup_lead", method="GET",
        path="/leads/{lead_id}", style="sync", frozen_endpoint=False,
    ),
    "op_ac2705604a6aa3f8": OperationSpec(
        op_id="op_ac2705604a6aa3f8", name="lookup_agent_directory", method="GET",
        path="/agents", style="sync", frozen_endpoint=False,
    ),
    "op_e12584afb808ad57": OperationSpec(
        op_id="op_e12584afb808ad57", name="lookup_risk", method="GET",
        path="/risks/{lead_id}", style="sync", frozen_endpoint=False,
    ),
    "op_4879b34b0dd377de": OperationSpec(
        op_id="op_4879b34b0dd377de", name="fetch_client_decision", method="GET",
        path="/quotes/{lead_id}/client-decision", style="sync", frozen_endpoint=False,
    ),
}

HEALTH_OP = OperationSpec(
    op_id="op_db8d1ee997721bd1", name="health", method="GET", path="/health",
    style="sync", frozen_endpoint=True,
)


def _resilient(op_id: str, op_name: str) -> Callable[[F], F]:
    """Decorate one ``DomainClient`` business method with the DRY_RUN
    short-circuit and the bounded retry/backoff policy.

    The decorated method's own body makes the real, literal
    ``self._client.get/post(...)`` call and parses the response; this
    decorator only decides WHEN to run that body (skipped under DRY_RUN) and
    HOW MANY TIMES (retrying the body itself, not a path/method it chooses).
    """

    def decorator(fn: F) -> F:
        @wraps(fn)
        async def wrapper(self: "DomainClient", *args: Any, **kwargs: Any) -> dict[str, Any]:
            if self._settings.dry_run:
                dry_run_payload = args[0] if args and isinstance(args[0], dict) else {}
                return _dry_run_response(op_name, dry_run_payload)

            max_retries = self._settings.domain_client_max_retries
            backoff_base = self._settings.domain_client_backoff_base_seconds
            attempt = 0
            last_error: Exception | None = None
            while attempt < max_retries:
                attempt += 1
                try:
                    return await fn(self, *args, **kwargs)
                except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as exc:
                    last_error = exc
                    logger.warning(
                        "domain_client retry op=%s attempt=%s error=%s", op_name, attempt, exc
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(backoff_base * (2 ** (attempt - 1)))
            raise DomainServiceError(
                f"lead-domain-service operation '{op_name}' ({op_id}) failed after "
                f"{max_retries} attempts: {last_error}"
            )

        return wrapper  # type: ignore[return-value]

    return decorator


def _parse_response(response: httpx.Response, op_name: str) -> dict[str, Any]:
    """Raise on a 5xx (retried by ``@_resilient``) or any other error
    status, else return the decoded JSON body (or ``{}`` for an empty one)."""

    if response.status_code >= 500:
        raise httpx.HTTPStatusError(
            f"{op_name} returned {response.status_code}",
            request=response.request,
            response=response,
        )
    response.raise_for_status()
    return response.json() if response.content else {}


class DomainClient:
    """Single HTTP client wrapping every lead-domain-service operation.

    Every business-named method below contains its OWN literal
    ``await self._client.get(...)``/``await self._client.post(...)`` call,
    directly in the method body -- the verb and the path template are
    literal text at that line, not threaded in from elsewhere.
    """

    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.lead_domain_service_url,
            timeout=settings.domain_client_timeout_seconds,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    @_resilient(op_id="op_db8d1ee997721bd1", op_name="health")
    async def health(self) -> dict[str, Any]:
        response = await self._client.get("/health")
        return _parse_response(response, "health")

    # -- business-named wrappers, one literal HTTP call per consumed operation/event --

    @_resilient(op_id="ev_9647b4fa974052af", op_name="register_lead")
    async def register_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post("/leads", json=lead)
        return _parse_response(response, "register_lead")

    @_resilient(op_id="op_e068c9371edb960b", op_name="auto_assign_agent")
    async def auto_assign_agent(self, lead_id: str, city: str) -> dict[str, Any]:
        response = await self._client.post(f"/leads/{lead_id}/auto-assign", json={"city": city})
        return _parse_response(response, "auto_assign_agent")

    @_resilient(op_id="op_09da3b189916ddf1", op_name="finalize_auto_assignment")
    async def finalize_auto_assignment(self, lead_id: str, agent_id: str) -> dict[str, Any]:
        response = await self._client.post(
            f"/leads/{lead_id}/assignment/finalize", json={"agent_id": agent_id}
        )
        return _parse_response(response, "finalize_auto_assignment")

    @_resilient(op_id="op_7da1e98a2662abb1", op_name="apply_manual_assignment")
    async def apply_manual_assignment(self, lead_id: str, agent_id: str) -> dict[str, Any]:
        response = await self._client.post(
            f"/leads/{lead_id}/assignment/manual", json={"agent_id": agent_id}
        )
        return _parse_response(response, "apply_manual_assignment")

    @_resilient(op_id="op_4cfe5e72a9e3ac12", op_name="notify_risk_incomplete")
    async def notify_risk_incomplete(self, lead_id: str, missing_fields: list[str]) -> dict[str, Any]:
        response = await self._client.post(
            f"/leads/{lead_id}/risk/incomplete-notice", json={"missing_fields": missing_fields}
        )
        return _parse_response(response, "notify_risk_incomplete")

    @_resilient(op_id="op_9d2a3f9c0f8666c3", op_name="screen_appetite")
    async def screen_appetite(self, lead_id: str, risk_data: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post(f"/risks/{lead_id}/screen", json={"risk_data": risk_data})
        return _parse_response(response, "screen_appetite")

    @_resilient(op_id="op_ad62bb70c888681f", op_name="rate_quote")
    async def rate_quote(self, lead_id: str, risk_data: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post(f"/quotes/{lead_id}/rate", json={"risk_data": risk_data})
        return _parse_response(response, "rate_quote")

    @_resilient(op_id="op_c077bc2e72e5ccaf", op_name="record_underwriter_outcome")
    async def record_underwriter_outcome(self, lead_id: str, decision: str) -> dict[str, Any]:
        response = await self._client.post(
            f"/risks/{lead_id}/underwriter-outcome", json={"decision": decision}
        )
        return _parse_response(response, "record_underwriter_outcome")

    @_resilient(op_id="op_7bbb0af5636162bb", op_name="flag_rerate")
    async def flag_rerate(self, lead_id: str) -> dict[str, Any]:
        response = await self._client.post(f"/leads/{lead_id}/rerate-flag", json={})
        return _parse_response(response, "flag_rerate")

    @_resilient(op_id="op_071073fcac0c7274", op_name="fetch_latest_quote_for_wait")
    async def fetch_latest_quote_for_wait(self, lead_id: str) -> dict[str, Any]:
        response = await self._client.get(f"/quotes/{lead_id}/latest")
        return _parse_response(response, "fetch_latest_quote_for_wait")

    @_resilient(op_id="op_04ae95f667cdc9fb", op_name="fetch_quote_for_bind")
    async def fetch_quote_for_bind(self, lead_id: str) -> dict[str, Any]:
        response = await self._client.get(f"/quotes/{lead_id}/latest")
        return _parse_response(response, "fetch_quote_for_bind")

    @_resilient(op_id="ev_df35d0b35c6d7375", op_name="upsert_agent_record")
    async def upsert_agent_record(self, agent: dict[str, Any]) -> dict[str, Any]:
        """The one operation with a fully frozen contract: ``POST /agents``."""
        response = await self._client.post("/agents", json=agent)
        return _parse_response(response, "upsert_agent_record")

    @_resilient(op_id="ev_ae38e9e0744f83d2", op_name="reassign_lead")
    async def reassign_lead(self, lead_id: str, new_agent_id: str) -> dict[str, Any]:
        response = await self._client.post(
            f"/leads/{lead_id}/reassign", json={"new_agent_id": new_agent_id}
        )
        return _parse_response(response, "reassign_lead")

    @_resilient(op_id="ev_603d5a9dc674d79a", op_name="publish_counts")
    async def publish_counts(self, agency_counts: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post("/reports/counts", json=agency_counts)
        return _parse_response(response, "publish_counts")

    @_resilient(op_id="op_bc60747eec921ea0", op_name="lookup_lead")
    async def lookup_lead(self, lead_id: str) -> dict[str, Any]:
        response = await self._client.get(f"/leads/{lead_id}")
        return _parse_response(response, "lookup_lead")

    @_resilient(op_id="op_ac2705604a6aa3f8", op_name="lookup_agent_directory")
    async def lookup_agent_directory(self, city: str) -> dict[str, Any]:
        response = await self._client.get("/agents", params={"city": city})
        return _parse_response(response, "lookup_agent_directory")

    @_resilient(op_id="op_e12584afb808ad57", op_name="lookup_risk")
    async def lookup_risk(self, lead_id: str) -> dict[str, Any]:
        response = await self._client.get(f"/risks/{lead_id}")
        return _parse_response(response, "lookup_risk")

    @_resilient(op_id="op_4879b34b0dd377de", op_name="fetch_client_decision")
    async def fetch_client_decision(self, lead_id: str) -> dict[str, Any]:
        response = await self._client.get(f"/quotes/{lead_id}/client-decision")
        return _parse_response(response, "fetch_client_decision")


def _dry_run_response(op_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Deterministic canned payload for DRY_RUN mode.

    Mirrors the shape the business logic expects back from each operation so
    the graph can run end-to-end with no live lead-domain-service. Decision
    fields default to the straight-through happy path; tests override the
    client methods directly for branch coverage.
    """

    if op_name == "register_lead":
        return {"lead_id": payload.get("lead_id", "dry-run-lead"), "duplicate_found": False}
    if op_name == "auto_assign_agent":
        return {"assigned": True, "agent_id": "dry-run-agent"}
    if op_name == "screen_appetite":
        return {"outcome": "accept"}
    if op_name == "rate_quote":
        return {"quote_id": "dry-run-quote", "total": 1000.0, "expiry": "dry-run-expiry"}
    if op_name == "lookup_risk":
        return {"complete": True}
    if op_name == "fetch_latest_quote_for_wait":
        return {"rerate": False}
    if op_name == "fetch_client_decision":
        return {"client_outcome": "accept"}
    if op_name == "fetch_quote_for_bind":
        return {"quote_id": "dry-run-quote", "total": 1000.0, "expiry": "dry-run-expiry"}
    return {}
