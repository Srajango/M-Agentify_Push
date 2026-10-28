"""initial schema: leads, risks, agents, quotes, policies, activities

Revision ID: 0001
Revises:
Create Date: 2026-10-21

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

LEAD_STATUS = sa.Enum(
    "New", "Capture", "Referred", "Approved", "Quoted", "Lost", "Converted", name="leadstatus"
)
COVERAGE_TYPE = sa.Enum("ThirdParty", "Comprehensive", name="coveragetype")
UNDERWRITER_OUTCOME = sa.Enum("Approved", "ApprovedWithLoading", "Declined", name="underwriteroutcome")
APPETITE_OUTCOME = sa.Enum("Clear", "Refer", "Decline", name="appetiteoutcome")
CONTACT_CHANNEL = sa.Enum("call", "meeting", "whatsapp", name="contactchannel")
CONTACT_OUTCOME = sa.Enum(
    "no_answer", "interested", "follow_up_booked", "not_interested", name="contactoutcome"
)
QUOTE_STATUS = sa.Enum("Active", "Replaced", "Accepted", "Expired", "Declined", name="quotestatus")


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("agent_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("city", sa.String(100), nullable=False, index=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "leads",
        sa.Column("lead_id", sa.String(36), primary_key=True),
        sa.Column("customer_name", sa.String(200), nullable=False),
        sa.Column("mobile_number", sa.String(20), nullable=False, index=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("product", sa.String(50), nullable=False, server_default="Private Car"),
        sa.Column("vehicle_registration_number", sa.String(20), nullable=False, index=True),
        sa.Column("status", LEAD_STATUS, nullable=False),
        sa.Column("lost_reason", sa.String(100), nullable=True),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.agent_id"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "risks",
        sa.Column("risk_id", sa.String(36), primary_key=True),
        sa.Column("lead_id", sa.String(36), sa.ForeignKey("leads.lead_id"), nullable=False),
        sa.Column("vehicle_make", sa.String(100), nullable=True),
        sa.Column("vehicle_model", sa.String(100), nullable=True),
        sa.Column("registration_year", sa.Integer, nullable=True),
        sa.Column("idv", sa.Numeric(12, 2), nullable=True),
        sa.Column("coverage_type", COVERAGE_TYPE, nullable=True),
        sa.Column("no_claim_bonus_fraction", sa.Numeric(4, 3), nullable=True),
        sa.Column("prior_claims_count", sa.Integer, nullable=True),
        sa.Column("is_complete", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("appetite_outcome", APPETITE_OUTCOME, nullable=True),
        sa.Column("appetite_reason", sa.String(200), nullable=True),
        sa.Column("underwriter_outcome", UNDERWRITER_OUTCOME, nullable=True),
        sa.Column("loading_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("decline_reason", sa.String(200), nullable=True),
        sa.Column("is_approved", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "quotes",
        sa.Column("quote_id", sa.String(36), primary_key=True),
        sa.Column("lead_id", sa.String(36), sa.ForeignKey("leads.lead_id"), nullable=False),
        sa.Column("risk_id", sa.String(36), sa.ForeignKey("risks.risk_id"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("coverage_type", COVERAGE_TYPE, nullable=False),
        sa.Column("idv", sa.Numeric(12, 2), nullable=False),
        sa.Column("own_damage_premium", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("third_party_premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("no_claim_bonus_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("loading_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", QUOTE_STATUS, nullable=False),
        sa.Column("rated_at", sa.DateTime, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "activities",
        sa.Column("activity_id", sa.String(36), primary_key=True),
        sa.Column("lead_id", sa.String(36), sa.ForeignKey("leads.lead_id"), nullable=False),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.agent_id"), nullable=False),
        sa.Column("channel", CONTACT_CHANNEL, nullable=False),
        sa.Column("outcome", CONTACT_OUTCOME, nullable=False),
        sa.Column("note", sa.Text, nullable=False),
        sa.Column("next_follow_up_date", sa.Date, nullable=True),
        sa.Column("occurred_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "policies",
        sa.Column("policy_id", sa.String(36), primary_key=True),
        sa.Column("lead_id", sa.String(36), sa.ForeignKey("leads.lead_id"), nullable=False),
        sa.Column("quote_id", sa.String(36), sa.ForeignKey("quotes.quote_id"), nullable=False),
        sa.Column("policy_number", sa.String(20), nullable=False, unique=True),
        sa.Column("coverage_type", COVERAGE_TYPE, nullable=False),
        sa.Column("idv", sa.Numeric(12, 2), nullable=False),
        sa.Column("premium_breakdown", sa.JSON, nullable=False),
        sa.Column("no_claim_bonus_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("loading_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column("issued_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("policies")
    op.drop_table("activities")
    op.drop_table("quotes")
    op.drop_table("risks")
    op.drop_table("leads")
    op.drop_table("agents")
