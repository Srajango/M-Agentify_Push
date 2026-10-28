"""Inbound workflow events from the gate-owning orchestrator: manual
assignment made, underwriter decision made, client accepted, client
declined. Logged for audit correlation; duplicate delivery is acknowledged,
not raised on."""

from __future__ import annotations

from fastapi import APIRouter

from lead_domain.events import record_inbound_workflow_event
from lead_domain.schemas import WorkflowEventAck, WorkflowEventIn

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/workflow-events", response_model=WorkflowEventAck)
def receive_workflow_event(payload: WorkflowEventIn) -> WorkflowEventAck:
    duplicate = record_inbound_workflow_event(payload.event_id, payload.event_type, payload.payload)
    return WorkflowEventAck(event_id=payload.event_id, status="received", duplicate=duplicate)
