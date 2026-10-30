"""Run-state model and in-memory run repository.

``RunState`` is the LangGraph state this service's graph carries through
every node (lead id, current node, pending gate, and every business field a
node reads or writes). ``RunRepository`` persists per-run bookkeeping (run
id, current step, per-step status/attempts/timestamps) separately from the
LangGraph checkpoint, so the status and SSE endpoints can read it without
reaching into checkpoint internals. No ``DATABASE_URL`` is configured for
this service (see .env.example), so storage is in-memory, matching the
role skill's instruction to use in-memory storage/checkpointing when no
database is wired.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, TypedDict

RunStatus = Literal["running", "awaiting_approval", "completed", "failed"]


class RunState(TypedDict, total=False):
    """State threaded through every node of the compiled graph."""

    run_id: str
    run_type: str  # "lead" | "agent_management" | "reassignment" | "access_report"
    current_node: str
    status: RunStatus

    # main lead pipeline
    lead: dict[str, Any]
    lead_id: Optional[str]
    duplicate_found: Optional[bool]
    agent_available_in_city: Optional[bool]
    assigned_agent_id: Optional[str]
    chosen_agent_id: Optional[str]
    risk_data: dict[str, Any]
    risk_complete: Optional[bool]
    screen_outcome: Optional[str]  # "decline" | "refer" | "accept"
    underwriter_decision: Optional[str]  # "approve" | "approve_with_loading" | "decline"
    quote: dict[str, Any]
    rerate: Optional[bool]
    rerate_count: int
    client_outcome: Optional[str]  # "accept" | "decline" | "expired"
    client_decline_reason: Optional[str]
    bind_inputs: dict[str, Any]
    policy: dict[str, Any]
    lost_reason: Optional[str]

    # side flows
    reassignment: dict[str, Any]
    access_report: dict[str, Any]
    agent_record: dict[str, Any]

    # bookkeeping
    result: dict[str, Any]
    error: Optional[str]


def new_run_state(run_id: str, run_type: str, payload: dict[str, Any]) -> RunState:
    """Build the initial state for a new run from the trigger request body."""

    state: RunState = {
        "run_id": run_id,
        "run_type": run_type,
        "current_node": "start",
        "status": "running",
        "lead": payload.get("lead", {}),
        "lead_id": payload.get("lead", {}).get("lead_id"),
        "risk_data": payload.get("risk_data", {}),
        "bind_inputs": payload.get("bind_inputs", {}),
        "quote": {},
        "rerate_count": 0,
        "policy": {},
        "reassignment": payload.get("reassignment", {}),
        "access_report": payload.get("access_report", {}),
        "agent_record": payload.get("agent_record", {}),
        "result": {},
    }
    return state


@dataclass
class StepRecord:
    step_id: str
    status: str
    attempts: int = 0
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    detail: Optional[str] = None


@dataclass
class Run:
    run_id: str
    run_type: str
    status: RunStatus = "running"
    current_node: str = "start"
    steps: list[StepRecord] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    resolved_gates: set[str] = field(default_factory=set)

    def record_step(self, step_id: str, status: str, detail: str | None = None) -> None:
        self.steps.append(StepRecord(step_id=step_id, status=status, detail=detail))
        self.current_node = step_id
        self.updated_at = time.time()


class RunRepository:
    """In-memory store of run bookkeeping, keyed by run id.

    Persisted on every transition via :meth:`record_transition`, not just at
    the end, so a process restart that still has this object alive (or a
    swapped-in persistent implementation) can answer "where did this run
    get to" at any point.
    """

    def __init__(self) -> None:
        self._runs: dict[str, Run] = {}

    def create(self, run_type: str) -> Run:
        run_id = str(uuid.uuid4())
        run = Run(run_id=run_id, run_type=run_type)
        run.record_step("start", "started")
        self._runs[run_id] = run
        return run

    def get(self, run_id: str) -> Optional[Run]:
        return self._runs.get(run_id)

    def record_transition(self, run_id: str, node: str, status: str, detail: str | None = None) -> None:
        run = self._runs.get(run_id)
        if run is None:
            return
        run.record_step(node, status, detail)

    def set_status(self, run_id: str, status: RunStatus) -> None:
        run = self._runs.get(run_id)
        if run is None:
            return
        run.status = status
        run.updated_at = time.time()
