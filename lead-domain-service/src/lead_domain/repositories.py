"""Data access layer. Every function takes a Session as a dependency —
repositories never open a connection themselves."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from lead_domain.models import Agent, Activity, Lead, LeadStatus, Policy, Quote, Risk


class LeadRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, lead: Lead) -> Lead:
        self.session.add(lead)
        self.session.flush()
        return lead

    def get(self, lead_id: str) -> Lead | None:
        return self.session.get(Lead, lead_id)

    def list_all(self) -> list[Lead]:
        return list(self.session.scalars(select(Lead).order_by(Lead.created_at)))

    def list_open_by_mobile_and_vehicle(
        self, mobile_number: str, vehicle_registration_number: str
    ) -> list[Lead]:
        """Sequential scan for an open (not Lost, not Converted) lead
        matching the same mobile number and vehicle registration number.
        Concurrent race conditions are explicitly out of scope (REQ-002)."""

        matches = []
        for lead in self.list_all():
            if (
                lead.mobile_number == mobile_number
                and lead.vehicle_registration_number == vehicle_registration_number
                and lead.status not in (LeadStatus.LOST, LeadStatus.CONVERTED)
            ):
                matches.append(lead)
        return matches

    def list_by_agent(self, agent_id: str) -> list[Lead]:
        return [lead for lead in self.list_all() if lead.agent_id == agent_id]

    def list_referred(self) -> list[Lead]:
        return [lead for lead in self.list_all() if lead.status == LeadStatus.REFERRED]


class AgentRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, agent: Agent) -> Agent:
        self.session.add(agent)
        self.session.flush()
        return agent

    def get(self, agent_id: str) -> Agent | None:
        return self.session.get(Agent, agent_id)

    def list_all(self) -> list[Agent]:
        return list(self.session.scalars(select(Agent).order_by(Agent.created_at)))

    def list_active_by_city(self, city: str) -> list[Agent]:
        return [a for a in self.list_all() if a.city == city and a.active]


class RiskRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, risk: Risk) -> Risk:
        self.session.add(risk)
        self.session.flush()
        return risk

    def list_for_lead(self, lead_id: str) -> list[Risk]:
        return list(
            self.session.scalars(
                select(Risk).where(Risk.lead_id == lead_id).order_by(Risk.created_at)
            )
        )

    def latest_for_lead(self, lead_id: str) -> Risk | None:
        risks = self.list_for_lead(lead_id)
        return risks[-1] if risks else None

    def latest_approved_for_lead(self, lead_id: str) -> Risk | None:
        approved = [r for r in self.list_for_lead(lead_id) if r.is_approved]
        if not approved:
            return None
        return max(approved, key=lambda r: r.approved_at or datetime.min)


class QuoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, quote: Quote) -> Quote:
        self.session.add(quote)
        self.session.flush()
        return quote

    def list_for_lead(self, lead_id: str) -> list[Quote]:
        return list(
            self.session.scalars(
                select(Quote).where(Quote.lead_id == lead_id).order_by(Quote.version)
            )
        )

    def latest_for_lead(self, lead_id: str) -> Quote | None:
        quotes = self.list_for_lead(lead_id)
        return quotes[-1] if quotes else None


class ActivityRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, activity: Activity) -> Activity:
        self.session.add(activity)
        self.session.flush()
        return activity

    def list_for_lead(self, lead_id: str) -> list[Activity]:
        return list(
            self.session.scalars(
                select(Activity).where(Activity.lead_id == lead_id).order_by(Activity.occurred_at)
            )
        )


class PolicyRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, policy: Policy) -> Policy:
        self.session.add(policy)
        self.session.flush()
        return policy

    def list_all(self) -> list[Policy]:
        return list(self.session.scalars(select(Policy)))

    def exists_with_number(self, policy_number: str) -> bool:
        return any(p.policy_number == policy_number for p in self.list_all())
