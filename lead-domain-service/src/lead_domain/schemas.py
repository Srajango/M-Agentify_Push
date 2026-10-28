"""Pydantic request/response schemas for every endpoint this service exposes.

These validate all incoming requests and outgoing responses at the HTTP
boundary, preventing shape mismatches from shipping to consumers.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Agents — frozen contract: POST /agents (op_9fcce42948fc43c0)
# ---------------------------------------------------------------------------


class AgentUpsertRequest(BaseModel):
    agent_id: Optional[str] = Field(default=None, description="Omit to create a new agent")
    name: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    active: bool


class AgentResponse(BaseModel):
    agent_id: str
    name: str
    city: str
    active: bool


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------


class LeadRegisterRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=200)
    mobile_number: str = Field(min_length=6, max_length=20)
    email: EmailStr
    city: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=100)
    vehicle_registration_number: str = Field(min_length=1, max_length=20)


class LeadResponse(BaseModel):
    lead_id: str
    customer_name: str
    mobile_number: str
    email: str
    city: str
    source: str
    product: str
    vehicle_registration_number: str
    status: str
    agent_id: Optional[str]
    lost_reason: Optional[str]
    created_at: datetime
    updated_at: datetime


class LeadReassignRequest(BaseModel):
    new_agent_id: str


# ---------------------------------------------------------------------------
# Risk capture, appetite screening, underwriting
# ---------------------------------------------------------------------------


class RiskSubmitRequest(BaseModel):
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    registration_year: Optional[int] = None
    idv: Optional[Decimal] = None
    coverage_type: Optional[Literal["ThirdParty", "Comprehensive"]] = None
    no_claim_bonus_fraction: Optional[Decimal] = None
    prior_claims_count: Optional[int] = None


class RiskResponse(BaseModel):
    risk_id: str
    lead_id: str
    vehicle_make: Optional[str]
    vehicle_model: Optional[str]
    registration_year: Optional[int]
    idv: Optional[Decimal]
    coverage_type: Optional[str]
    no_claim_bonus_fraction: Optional[Decimal]
    prior_claims_count: Optional[int]
    is_complete: bool
    missing_fields: list[str]
    appetite_outcome: Optional[str]
    appetite_reason: Optional[str]
    underwriter_outcome: Optional[str]
    loading_percent: Optional[Decimal]
    decline_reason: Optional[str]
    is_approved: bool
    lead_status: str


class UnderwriterOutcomeRequest(BaseModel):
    outcome: Literal["Approved", "ApprovedWithLoading", "Declined"]
    loading_percent: Optional[Decimal] = None


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------


class QuoteResponse(BaseModel):
    quote_id: str
    lead_id: str
    risk_id: str
    version: int
    coverage_type: str
    idv: float
    own_damage_premium: float
    third_party_premium: float
    no_claim_bonus_amount: float
    loading_amount: float
    total_premium: float
    status: str
    rated_at: datetime
    expires_at: datetime
    lead_status: str


# ---------------------------------------------------------------------------
# Contact activities
# ---------------------------------------------------------------------------


class ActivityCreateRequest(BaseModel):
    agent_id: str
    channel: Literal["call", "meeting", "whatsapp"]
    outcome: Literal["no_answer", "interested", "follow_up_booked", "not_interested"]
    note: str = Field(min_length=1)
    next_follow_up_date: Optional[date] = None


class ActivityResponse(BaseModel):
    activity_id: str
    lead_id: str
    agent_id: str
    channel: str
    outcome: str
    note: str
    next_follow_up_date: Optional[date]
    occurred_at: datetime


# ---------------------------------------------------------------------------
# Client decision (accept / decline / expiry)
# ---------------------------------------------------------------------------


class ClientDecisionRequest(BaseModel):
    action: Literal["accept", "decline"]
    reason: Optional[Literal["price", "bought_elsewhere", "not_interested"]] = None


class ClientDecisionResponse(BaseModel):
    lead_id: str
    lead_status: str
    lost_reason: Optional[str] = None
    quote_id: Optional[str] = None
    quote_status: Optional[str] = None
    total_premium: Optional[float] = None
    expires_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Bind and policy issuance
# ---------------------------------------------------------------------------


class BindRequest(BaseModel):
    effective_date: date
    collected_amount: Decimal


class BindResponse(BaseModel):
    policy_number: str
    lead_id: str
    lead_status: str
    coverage_type: str
    idv: Decimal
    premium_breakdown: dict
    no_claim_bonus_amount: Decimal
    loading_amount: Decimal
    effective_date: date
    issued_at: datetime


# ---------------------------------------------------------------------------
# Role-based visibility and reporting
# ---------------------------------------------------------------------------


class AgentCounts(BaseModel):
    agent_id: str
    name: str
    assigned: int
    open: int
    converted: int
    lost: int
    conversion_rate: float


class AgencyCounts(BaseModel):
    assigned: int
    open: int
    converted: int
    lost: int
    conversion_rate: float


class CountsResponse(BaseModel):
    agents: list[AgentCounts]
    agency: AgencyCounts


class LeadListResponse(BaseModel):
    role: str
    leads: list[LeadResponse]
    counts: Optional[CountsResponse] = None


# ---------------------------------------------------------------------------
# Inbound workflow events (from the gate-owning orchestrator)
# ---------------------------------------------------------------------------


class WorkflowEventIn(BaseModel):
    event_id: str
    event_type: Literal[
        "manual_assignment_made",
        "underwriter_decision_made",
        "client_accepted",
        "client_declined",
    ]
    lead_id: Optional[str] = None
    payload: dict = Field(default_factory=dict)


class WorkflowEventAck(BaseModel):
    event_id: str
    status: str
    duplicate: bool


# ---------------------------------------------------------------------------
# Structured error envelope
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
