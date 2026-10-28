"""Application runtime: wires the domain client, event publisher, run
repository and the compiled graph into the operations the HTTP routers call.

One ``OrchestratorRuntime`` instance lives for the process lifetime (built in
``main.py``'s lifespan) so the in-memory run repository and LangGraph
checkpointer survive across requests for the same run id.
"""

from __future__ import annotations

from typing import Any

from .config import Settings, get_settings
from .domain_client import DomainClient
from .events import EventPublisher
from .exceptions import GateNotAwaitingApprovalError, RunNotFoundError, ValidationError
from .graph import build_graph
from .state import Run, RunRepository, new_run_state

RUN_TYPES = ("lead", "agent_management", "reassignment", "access_report")


class OrchestratorRuntime:
    """Owns this process's domain client, event bus, run store and graph."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = DomainClient(self.settings)
        self.events = EventPublisher()
        self.runs = RunRepository()
        self.graph = build_graph(self.client, self.events)

    async def aclose(self) -> None:
        await self.client.aclose()

    @staticmethod
    def _config(run_id: str) -> dict[str, Any]:
        # The re-rate loop and the risk-capture loop can each revisit a node
        # a bounded number of times; raise LangGraph's default recursion
        # limit so a legitimate multi-iteration run never hits it.
        return {"configurable": {"thread_id": run_id}, "recursion_limit": 100}

    async def _advance(self, run: Run, initial_state: dict[str, Any] | None) -> dict[str, Any]:
        config = self._config(run.run_id)
        try:
            result = await self.graph.ainvoke(initial_state, config=config)
        except Exception:
            self.runs.set_status(run.run_id, "failed")
            raise
        snapshot = await self.graph.aget_state(config)
        if snapshot.next:
            gate = snapshot.next[0]
            self.runs.set_status(run.run_id, "awaiting_approval")
            self.runs.record_transition(run.run_id, gate, "awaiting_approval")
        else:
            status = result.get("status", "running")
            self.runs.set_status(run.run_id, status)
            self.runs.record_transition(run.run_id, result.get("current_node", run.current_node), status)
        return result

    async def start_run(self, run_type: str, payload: dict[str, Any]) -> tuple[Run, dict[str, Any]]:
        if run_type not in RUN_TYPES:
            raise ValidationError(f"run_type must be one of {RUN_TYPES}")
        run = self.runs.create(run_type)
        state = new_run_state(run.run_id, run_type, payload)
        result = await self._advance(run, state)
        return run, result

    def get_run(self, run_id: str) -> Run:
        run = self.runs.get(run_id)
        if run is None:
            raise RunNotFoundError(f"run '{run_id}' not found")
        return run

    async def _resume_gate(self, run_id: str, node_key: str, state_update: dict[str, Any]) -> dict[str, Any]:
        run = self.get_run(run_id)
        if node_key in run.resolved_gates:
            # Idempotent: the gate already resumed once, never apply it twice.
            return {"run_id": run.run_id, "status": run.status, "current_node": run.current_node}
        if run.status != "awaiting_approval" or run.current_node != node_key:
            raise GateNotAwaitingApprovalError(
                f"run '{run_id}' is not awaiting approval at gate '{node_key}'"
            )
        config = self._config(run_id)
        await self.graph.aupdate_state(config, state_update)
        result = await self._advance(run, None)
        run.resolved_gates.add(node_key)
        return result

    async def approve_manager_assignment(self, run_id: str, agent_id: str) -> dict[str, Any]:
        if not agent_id:
            raise ValidationError("agent_id is required to resume manager_manual_assign")
        return await self._resume_gate(run_id, "manager_manual_assign", {"chosen_agent_id": agent_id})

    async def approve_underwriter_referral(self, run_id: str, decision: str) -> dict[str, Any]:
        if decision not in ("approve", "approve_with_loading"):
            raise ValidationError("decision must be 'approve' or 'approve_with_loading'")
        return await self._resume_gate(
            run_id, "underwriter_review_referral", {"underwriter_decision": decision}
        )

    async def reject_underwriter_referral(self, run_id: str) -> dict[str, Any]:
        return await self._resume_gate(
            run_id, "underwriter_review_referral", {"underwriter_decision": "decline"}
        )
