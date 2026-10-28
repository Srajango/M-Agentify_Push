"""SQLAlchemy ORM models for the Lead, Risk, Agent, Quote, Policy and Activity
tables. Production schema changes are applied by the authored Alembic
migrations under migrations/versions/; this module is also used directly by
the in-process SQLite fallback via Base.metadata.create_all (see db.py).
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Date, Boolean, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class LeadStatus(str, enum.Enum):
    NEW = "New"
    CAPTURE = "Capture"
    REFERRED = "Referred"
    APPROVED = "Approved"
    QUOTED = "Quoted"
    LOST = "Lost"
    CONVERTED = "Converted"


class CoverageType(str, enum.Enum):
    THIRD_PARTY = "ThirdParty"
    COMPREHENSIVE = "Comprehensive"


class UnderwriterOutcome(str, enum.Enum):
    APPROVED = "Approved"
    APPROVED_WITH_LOADING = "ApprovedWithLoading"
    DECLINED = "Declined"


class AppetiteOutcome(str, enum.Enum):
    CLEAR = "Clear"
    REFER = "Refer"
    DECLINE = "Decline"


class ContactChannel(str, enum.Enum):
    CALL = "call"
    MEETING = "meeting"
    WHATSAPP = "whatsapp"


class ContactOutcome(str, enum.Enum):
    NO_ANSWER = "no_answer"
    INTERESTED = "interested"
    FOLLOW_UP_BOOKED = "follow_up_booked"
    NOT_INTERESTED = "not_interested"


class QuoteStatus(str, enum.Enum):
    ACTIVE = "Active"
    REPLACED = "Replaced"
    ACCEPTED = "Accepted"
    EXPIRED = "Expired"
    DECLINED = "Declined"


class Agent(Base):
    __tablename__ = "agents"

    agent_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    leads: Mapped[list["Lead"]] = relationship(back_populates="agent")


class Lead(Base):
    __tablename__ = "leads"

    lead_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    mobile_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    product: Mapped[str] = mapped_column(String(50), nullable=False, default="Private Car")
    vehicle_registration_number: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), nullable=False, default=LeadStatus.NEW
    )
    lost_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("agents.agent_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    agent: Mapped[Agent | None] = relationship(back_populates="leads")
    risks: Mapped[list["Risk"]] = relationship(back_populates="lead", order_by="Risk.created_at")
    quotes: Mapped[list["Quote"]] = relationship(back_populates="lead", order_by="Quote.version")
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="lead", order_by="Activity.occurred_at"
    )
    policies: Mapped[list["Policy"]] = relationship(back_populates="lead")


class Risk(Base):
    __tablename__ = "risks"

    risk_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.lead_id"), nullable=False)
    vehicle_make: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vehicle_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    registration_year: Mapped[int | None] = mapped_column(nullable=True)
    idv: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    coverage_type: Mapped[CoverageType | None] = mapped_column(Enum(CoverageType), nullable=True)
    no_claim_bonus_fraction: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    prior_claims_count: Mapped[int | None] = mapped_column(nullable=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    appetite_outcome: Mapped[AppetiteOutcome | None] = mapped_column(
        Enum(AppetiteOutcome), nullable=True
    )
    appetite_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    underwriter_outcome: Mapped[UnderwriterOutcome | None] = mapped_column(
        Enum(UnderwriterOutcome), nullable=True
    )
    loading_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    decline_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    lead: Mapped[Lead] = relationship(back_populates="risks")


class Quote(Base):
    __tablename__ = "quotes"

    quote_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.lead_id"), nullable=False)
    risk_id: Mapped[str] = mapped_column(String(36), ForeignKey("risks.risk_id"), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    coverage_type: Mapped[CoverageType] = mapped_column(Enum(CoverageType), nullable=False)
    idv: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    own_damage_premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    third_party_premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    no_claim_bonus_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    loading_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[QuoteStatus] = mapped_column(
        Enum(QuoteStatus), nullable=False, default=QuoteStatus.ACTIVE
    )
    rated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    lead: Mapped[Lead] = relationship(back_populates="quotes")


class Activity(Base):
    __tablename__ = "activities"

    activity_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.lead_id"), nullable=False)
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agents.agent_id"), nullable=False
    )
    channel: Mapped[ContactChannel] = mapped_column(Enum(ContactChannel), nullable=False)
    outcome: Mapped[ContactOutcome] = mapped_column(Enum(ContactOutcome), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    next_follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lead: Mapped[Lead] = relationship(back_populates="activities")


class Policy(Base):
    __tablename__ = "policies"

    policy_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.lead_id"), nullable=False)
    quote_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("quotes.quote_id"), nullable=False
    )
    policy_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    coverage_type: Mapped[CoverageType] = mapped_column(Enum(CoverageType), nullable=False)
    idv: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    premium_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    no_claim_bonus_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    loading_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lead: Mapped[Lead] = relationship(back_populates="policies")
