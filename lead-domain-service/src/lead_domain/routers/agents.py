"""POST /agents — frozen contract op_9fcce42948fc43c0 (upsert_agent_record).
Node: manage_agent_records."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lead_domain.deps import session_dependency
from lead_domain.mappers import agent_to_dict
from lead_domain.process_graph import get_handler
from lead_domain.repositories import AgentRepository
from lead_domain.schemas import AgentResponse, AgentUpsertRequest

router = APIRouter(tags=["agents"])


@router.post("/agents", response_model=AgentResponse, status_code=200)
def upsert_agent_record(
    payload: AgentUpsertRequest, session: Session = Depends(session_dependency)
) -> AgentResponse:
    result = get_handler("manage_agent_records")({"session": session, "payload": payload})
    return AgentResponse.model_validate(result)


@router.get("/agents", response_model=list[AgentResponse])
def list_agents(
    city: Optional[str] = None,
    active: Optional[bool] = None,
    session: Session = Depends(session_dependency),
) -> list[AgentResponse]:
    """Agent roster lookup used by round-robin assignment and by managers
    maintaining coverage — filterable by city and active status."""

    agents = AgentRepository(session).list_all()
    if city is not None:
        agents = [a for a in agents if a.city == city]
    if active is not None:
        agents = [a for a in agents if a.active == active]
    return [AgentResponse.model_validate(agent_to_dict(a)) for a in agents]
