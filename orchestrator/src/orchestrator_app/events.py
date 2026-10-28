"""Lifecycle event publishing.

The approved plan (task 5) requires one event at each of four milestones:
agent assignment finalized, lead lost, quote generated/re-rated, and policy
issued. No event-bus transport (broker URL, topic, webhook) is named in this
service's tech_stack or frozen contract, so publishing fans out to any
registered sink -- by default an in-process log sink -- rather than
inventing infrastructure that was never declared (see GAPS.json).

The four ``start -> *`` edges in the contract's ``service.publishes`` list
(one per sub-flow this orchestrator dispatches to) are published the same
way, at the moment the trigger routes a run into that sub-flow.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class EventSink(Protocol):
    def __call__(self, event_type: str, run_id: str, payload: dict[str, Any]) -> None: ...


def log_sink(event_type: str, run_id: str, payload: dict[str, Any]) -> None:
    logger.info("event published type=%s run_id=%s payload=%s", event_type, run_id, payload)


@dataclass
class EventPublisher:
    """Publishes lifecycle events to every registered sink.

    ``published`` records every event fired during the publisher's lifetime
    so tests and the run repository can assert "exactly once per milestone".
    """

    sinks: list[EventSink] = field(default_factory=lambda: [log_sink])
    published: list[dict[str, Any]] = field(default_factory=list)

    def publish(self, event_type: str, run_id: str, payload: dict[str, Any] | None = None) -> None:
        record = {"event_type": event_type, "run_id": run_id, "payload": payload or {}}
        self.published.append(record)
        for sink in self.sinks:
            sink(event_type, run_id, payload or {})


# -- milestone event names (task 5) -------------------------------------------

EVENT_AGENT_ASSIGNED = "lead.agent_assigned"
EVENT_LEAD_LOST = "lead.lost"
EVENT_QUOTE_ISSUED = "lead.quote_issued"
EVENT_POLICY_ISSUED = "lead.policy_issued"

# -- service.publishes edges (sub-flow dispatch) -------------------------------

EVENT_LEAD_FLOW_STARTED = "flow.lead_intake_started"
EVENT_AGENT_MANAGEMENT_STARTED = "flow.agent_management_started"
EVENT_REASSIGNMENT_STARTED = "flow.reassignment_started"
EVENT_ACCESS_REPORT_STARTED = "flow.access_report_started"
