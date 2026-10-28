"""Health, trigger and run-status/SSE routes."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ..runtime import OrchestratorRuntime
from ..schemas import HealthResponse, RunDetailResponse, RunResponse, RunStepResponse, TriggerRequest

router = APIRouter()


def get_runtime(request: Request) -> OrchestratorRuntime:
    return request.app.state.runtime


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/runs", response_model=RunResponse, status_code=201)
async def trigger_run(body: TriggerRequest, request: Request) -> RunResponse:
    """Starts a new run and drives the compiled graph to its first halt.

    This invokes the compiled graph (``graph.ainvoke``) rather than merely
    storing initial state -- the full main pipeline, reassignment, or
    access-and-reporting sub-flow runs here, pausing at a human gate or a
    terminal node as the process model dictates.
    """

    runtime = get_runtime(request)
    payload = body.model_dump(exclude_none=True)
    run, _ = await runtime.start_run(body.run_type, payload)
    return RunResponse(run_id=run.run_id, run_type=run.run_type, status=run.status, current_node=run.current_node)


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_run(run_id: str, request: Request) -> RunDetailResponse:
    runtime = get_runtime(request)
    run = runtime.get_run(run_id)
    return RunDetailResponse(
        run_id=run.run_id,
        run_type=run.run_type,
        status=run.status,
        current_node=run.current_node,
        steps=[
            RunStepResponse(step_id=s.step_id, status=s.status, attempts=s.attempts, detail=s.detail)
            for s in run.steps
        ],
    )


def _sse_payload(run_id: str, step_id: str, status: str, detail: str | None = None) -> str:
    data = {"run_id": run_id, "step_id": step_id, "status": status, "detail": detail}
    return f"data: {json.dumps(data)}\n\n"


async def _event_stream(runtime: OrchestratorRuntime, run_id: str):
    run = runtime.get_run(run_id)
    sent = 0
    for step in run.steps:
        yield _sse_payload(run.run_id, step.step_id, step.status, step.detail)
        sent += 1
    polls = 0
    while run.status not in ("completed", "failed") and polls < 200:
        await asyncio.sleep(0.05)
        polls += 1
        if len(run.steps) > sent:
            for step in run.steps[sent:]:
                yield _sse_payload(run.run_id, step.step_id, step.status, step.detail)
                sent += 1
    yield _sse_payload(run.run_id, run.current_node, run.status, "run finished or stream timed out")


@router.get("/runs/{run_id}/events")
async def run_events(run_id: str, request: Request) -> StreamingResponse:
    runtime = get_runtime(request)
    runtime.get_run(run_id)  # raises RunNotFoundError (-> 404) if missing
    return StreamingResponse(_event_stream(runtime, run_id), media_type="text/event-stream")
