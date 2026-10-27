"""FastAPI application entrypoint for the Lead-to-Policy Orchestrator.

Run with: ``uvicorn orchestrator_app.main:app`` (see Dockerfile CMD).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import OrchestratorError
from .routers import gates, runs
from .runtime import OrchestratorRuntime


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    runtime = OrchestratorRuntime()
    app.state.runtime = runtime
    try:
        yield
    finally:
        await runtime.aclose()


app = FastAPI(title="Lead-to-Policy Orchestrator", version="1.0.0", lifespan=lifespan)

app.include_router(runs.router)
app.include_router(gates.router)


@app.exception_handler(OrchestratorError)
async def orchestrator_error_handler(request: Request, exc: OrchestratorError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_type": exc.error_type, "message": exc.message},
    )
