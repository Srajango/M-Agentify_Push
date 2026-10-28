"""Request/response schemas for the orchestrator's own HTTP surface.

These validate every incoming request at the boundary; a request missing a
required field gets a 422 from FastAPI before it ever reaches the graph.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class LeadPayload(BaseModel):
    """Fields captured at lead intake (Register New Lead)."""

    lead_id: Optional[str] = None
    customer_name: str
    mobile_number: str
    email: EmailStr
    city: str
    source: str
    vehicle_reg: str
    rerate_requested_count: int = 0


class TriggerRequest(BaseModel):
    """Body for ``POST /runs`` -- starts one of the four sub-flows."""

    run_type: Literal["lead", "agent_management", "reassignment", "access_report"]
    lead: Optional[LeadPayload] = None
    risk_data: dict[str, Any] = Field(default_factory=dict)
    bind_inputs: dict[str, Any] = Field(default_factory=dict)
    reassignment: dict[str, Any] = Field(default_factory=dict)
    agent_record: dict[str, Any] = Field(default_factory=dict)
    access_report: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _require_subflow_payload(self) -> "TriggerRequest":
        if self.run_type == "lead" and self.lead is None:
            raise ValueError("lead is required when run_type is 'lead'")
        if self.run_type == "reassignment" and not self.reassignment.get("lead_id"):
            raise ValueError("reassignment.lead_id is required when run_type is 'reassignment'")
        if self.run_type == "agent_management" and not self.agent_record:
            raise ValueError("agent_record is required when run_type is 'agent_management'")
        if self.run_type == "access_report" and not self.access_report:
            raise ValueError("access_report is required when run_type is 'access_report'")
        return self


class RunResponse(BaseModel):
    run_id: str
    run_type: str
    status: str
    current_node: str


class RunStepResponse(BaseModel):
    step_id: str
    status: str
    attempts: int
    detail: Optional[str] = None


class RunDetailResponse(RunResponse):
    steps: list[RunStepResponse]


class ManagerAssignApproveRequest(BaseModel):
    """Body for resuming ``manager_manual_assign`` with the manager's choice."""

    agent_id: str


class UnderwriterApproveRequest(BaseModel):
    """Body for resuming ``underwriter_review_referral`` on approval."""

    decision: Literal["approve", "approve_with_loading"]


class HealthResponse(BaseModel):
    status: str
