"""Publishes this service's domain events to the orchestrator event bus, and
records inbound workflow events for audit correlation.

DRY_RUN switches exactly one seam: whether `publish` sends a real HTTP
request. The four domain events (lead-registered, lead-status-changed,
quote-issued, policy-issued) are always computed and logged the same way —
only the outbound transport changes.
"""

from __future__ import annotations

from typing import Any

import httpx

from lead_domain.config import Settings
from lead_domain.logging_config import get_logger

logger = get_logger("events")

LEAD_REGISTERED = "lead-registered"
LEAD_STATUS_CHANGED = "lead-status-changed"
QUOTE_ISSUED = "quote-issued"
POLICY_ISSUED = "policy-issued"


class EventPublisher:
    """One transport seam (`_send`) toggled by `settings.dry_run`. The
    httpx.Client is only opened when a real send is about to happen, so a
    DRY_RUN=true request never allocates a socket it will not use."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self._settings = settings
        self._client = client

    def publish(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        envelope = {"event_type": event_type, "payload": payload}
        if self._settings.dry_run:
            logger.info("event_logged event_type=%s payload=%s", event_type, payload)
            return {"status": "logged", "event_type": event_type}
        return self._send(envelope)

    def _send(self, envelope: dict[str, Any]) -> dict[str, Any]:
        client = self._client or httpx.Client(timeout=10.0)
        response = client.post(self._settings.orchestrator_events_url, json=envelope)
        response.raise_for_status()
        logger.info("event_sent event_type=%s", envelope["event_type"])
        return response.json()

    def lead_registered(self, lead_id: str, status: str) -> dict[str, Any]:
        return self.publish(LEAD_REGISTERED, {"lead_id": lead_id, "status": status})

    def lead_status_changed(
        self, lead_id: str, previous_status: str, new_status: str, reason: str | None = None
    ) -> dict[str, Any]:
        return self.publish(
            LEAD_STATUS_CHANGED,
            {
                "lead_id": lead_id,
                "previous_status": previous_status,
                "new_status": new_status,
                "reason": reason,
            },
        )

    def quote_issued(self, lead_id: str, quote_id: str, version: int, total_premium: str) -> dict[str, Any]:
        return self.publish(
            QUOTE_ISSUED,
            {
                "lead_id": lead_id,
                "quote_id": quote_id,
                "version": version,
                "total_premium": total_premium,
            },
        )

    def policy_issued(self, lead_id: str, policy_id: str, policy_number: str) -> dict[str, Any]:
        return self.publish(
            POLICY_ISSUED,
            {"lead_id": lead_id, "policy_id": policy_id, "policy_number": policy_number},
        )


_seen_event_ids: set[str] = set()


def record_inbound_workflow_event(event_id: str, event_type: str, payload: dict[str, Any]) -> bool:
    """Log an inbound workflow event from the gate-owning service for audit
    correlation. Returns True if this event_id was already seen (duplicate
    delivery), in which case it is logged but not treated as an error."""

    duplicate = event_id in _seen_event_ids
    _seen_event_ids.add(event_id)
    logger.info(
        "workflow_event_received event_id=%s event_type=%s duplicate=%s payload=%s",
        event_id,
        event_type,
        duplicate,
        payload,
    )
    return duplicate


def reset_seen_events() -> None:
    """Test helper: clear the in-memory dedupe set between test cases."""

    _seen_event_ids.clear()
