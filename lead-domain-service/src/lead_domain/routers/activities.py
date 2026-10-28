"""Agent contact activities — node: record_contact_activity."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lead_domain.deps import session_dependency
from lead_domain.mappers import activity_to_dict
from lead_domain.process_graph import get_handler
from lead_domain.repositories import ActivityRepository
from lead_domain.schemas import ActivityCreateRequest, ActivityResponse

router = APIRouter(tags=["activities"])


@router.post("/leads/{lead_id}/activities", response_model=ActivityResponse, status_code=201)
def record_contact_activity(
    lead_id: str, payload: ActivityCreateRequest, session: Session = Depends(session_dependency)
) -> ActivityResponse:
    """Node: record_contact_activity (REQ-011). Append-only: there is no
    update or delete route for an activity anywhere in this service."""

    result = get_handler("record_contact_activity")(
        {"session": session, "lead_id": lead_id, "payload": payload}
    )
    return ActivityResponse.model_validate(result)


@router.get("/leads/{lead_id}/activities", response_model=list[ActivityResponse])
def list_activities(lead_id: str, session: Session = Depends(session_dependency)) -> list[ActivityResponse]:
    activities = ActivityRepository(session).list_for_lead(lead_id)
    return [ActivityResponse.model_validate(activity_to_dict(a)) for a in activities]
