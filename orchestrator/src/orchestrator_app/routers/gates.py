"""Human-gate resume/reject routes.

``manager_manual_assign`` only has a resume operation (no reject is named in
the frozen contract's ``human_gates`` block). ``underwriter_review_referral``
has both resume and reject. Both are idempotent: calling resume/reject again
after the gate already resumed is a no-op (see ``OrchestratorRuntime._resume_gate``).
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from ..runtime import OrchestratorRuntime
from ..schemas import ManagerAssignApproveRequest, RunResponse, UnderwriterApproveRequest

router = APIRouter()


def get_runtime(request: Request) -> OrchestratorRuntime:
    return request.app.state.runtime


@router.post("/runs/{run_id}/steps/manager_manual_assign/approve", response_model=RunResponse)
async def approve_manager_assignment(
    run_id: str, body: ManagerAssignApproveRequest, request: Request
) -> RunResponse:
    runtime = get_runtime(request)
    result = await runtime.approve_manager_assignment(run_id, body.agent_id)
    run = runtime.get_run(run_id)
    return RunResponse(
        run_id=run.run_id,
        run_type=run.run_type,
        status=result.get("status", run.status),
        current_node=result.get("current_node", run.current_node),
    )


@router.post("/runs/{run_id}/steps/underwriter_review_referral/approve", response_model=RunResponse)
async def approve_underwriter_referral(
    run_id: str, body: UnderwriterApproveRequest, request: Request
) -> RunResponse:
    runtime = get_runtime(request)
    result = await runtime.approve_underwriter_referral(run_id, body.decision)
    run = runtime.get_run(run_id)
    return RunResponse(
        run_id=run.run_id,
        run_type=run.run_type,
        status=result.get("status", run.status),
        current_node=result.get("current_node", run.current_node),
    )


@router.post("/runs/{run_id}/steps/underwriter_review_referral/reject", response_model=RunResponse)
async def reject_underwriter_referral(run_id: str, request: Request) -> RunResponse:
    runtime = get_runtime(request)
    result = await runtime.reject_underwriter_referral(run_id)
    run = runtime.get_run(run_id)
    return RunResponse(
        run_id=run.run_id,
        run_type=run.run_type,
        status=result.get("status", run.status),
        current_node=result.get("current_node", run.current_node),
    )
