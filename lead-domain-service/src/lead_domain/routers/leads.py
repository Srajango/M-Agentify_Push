"""Lead registration, round-robin/manual assignment and manager
reassignment. Nodes: register_lead, auto_assign_agent,
manager_reassign_lead."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from lead_domain.deps import publisher_dependency, session_dependency
from lead_domain.events import EventPublisher
from lead_domain.exceptions import NotFoundError
from lead_domain.mappers import lead_to_dict
from lead_domain.process_graph import get_handler
from lead_domain.repositories import LeadRepository
from lead_domain.schemas import LeadReassignRequest, LeadRegisterRequest, LeadResponse

router = APIRouter(tags=["leads"])


@router.post("/leads", response_model=LeadResponse, status_code=201)
def register_lead(
    payload: LeadRegisterRequest,
    session: Session = Depends(session_dependency),
    publisher: EventPublisher = Depends(publisher_dependency),
) -> LeadResponse:
    """Registers the lead (REQ-001, REQ-002) then immediately runs
    round-robin assignment (REQ: a lead whose city has an active agent is
    never left unassigned)."""

    result = get_handler("register_lead")({"session": session, "publisher": publisher, "payload": payload})
    lead_id = result["lead_id"]
    get_handler("auto_assign_agent")({"session": session, "lead_id": lead_id})

    leads = LeadRepository(session)
    lead = leads.get(lead_id)
    assert lead is not None
    return LeadResponse.model_validate(lead_to_dict(lead))


@router.get("/leads/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: str, session: Session = Depends(session_dependency)) -> LeadResponse:
    lead = LeadRepository(session).get(lead_id)
    if lead is None:
        raise NotFoundError(f"lead '{lead_id}' not found")
    return LeadResponse.model_validate(lead_to_dict(lead))


@router.post("/leads/{lead_id}/assign", response_model=LeadResponse)
def assign_agent(
    lead_id: str,
    manager_agent_id: Optional[str] = Query(default=None),
    session: Session = Depends(session_dependency),
) -> LeadResponse:
    """Node: auto_assign_agent. Round-robin among active agents in the
    lead's city, or the manager's chosen agent_id when supplied."""

    get_handler("auto_assign_agent")(
        {"session": session, "lead_id": lead_id, "manager_agent_id": manager_agent_id}
    )
    lead = LeadRepository(session).get(lead_id)
    assert lead is not None
    return LeadResponse.model_validate(lead_to_dict(lead))


@router.post("/leads/{lead_id}/reassign", response_model=LeadResponse)
def reassign_lead(
    lead_id: str, payload: LeadReassignRequest, session: Session = Depends(session_dependency)
) -> LeadResponse:
    """Node: manager_reassign_lead (REQ-016)."""

    result = get_handler("manager_reassign_lead")(
        {"session": session, "lead_id": lead_id, "new_agent_id": payload.new_agent_id}
    )
    return LeadResponse.model_validate(result)
