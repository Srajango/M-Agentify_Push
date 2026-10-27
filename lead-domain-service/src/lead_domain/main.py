"""Creates the FastAPI() instance and wires everything together. This is
the module the Dockerfile CMD boots: `uvicorn lead_domain.main:app`."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from lead_domain.exceptions import LeadDomainServiceError
from lead_domain.logging_config import get_logger
from lead_domain.process_graph import validate_graph
from lead_domain.routers import activities, agents, bind, decisions, health, leads, quotes, reporting, risk, webhooks
from lead_domain.schemas import ErrorDetail, ErrorResponse

# Importing the services package registers every process-graph node handler
# (register_lead, auto_assign_agent, manage_agent_records, capture_risk_data,
# auto_screen_appetite, record_underwriter_outcome, auto_rate_quote,
# record_contact_activity, client_decision_wait, validate_bind_inputs,
# bind_and_issue_policy, manager_reassign_lead, role_based_access_control,
# compute_counts_conversion) before the graph is validated below.
from lead_domain import services  # noqa: F401

logger = get_logger("main")

app = FastAPI(title="Lead & Policy Domain Service", version="0.1.0")

app.include_router(health.router)
app.include_router(agents.router)
app.include_router(leads.router)
app.include_router(risk.router)
app.include_router(quotes.router)
app.include_router(activities.router)
app.include_router(decisions.router)
app.include_router(bind.router)
app.include_router(reporting.router)
app.include_router(webhooks.router)


@app.exception_handler(LeadDomainServiceError)
async def domain_error_handler(request: Request, exc: LeadDomainServiceError) -> JSONResponse:
    logger.info(
        "request_error path=%s error_code=%s message=%s", request.url.path, exc.error_code, exc.message
    )
    envelope = ErrorResponse(error=ErrorDetail(code=exc.error_code, message=exc.message))
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())


@app.on_event("startup")
def on_startup() -> None:
    validate_graph()
    logger.info("startup_complete nodes=%d", 14)
