# Lead-to-Policy Orchestrator

FastAPI + LangGraph service that owns the control-flow skeleton of the
private-car lead lifecycle: the `start` node, every decision node, the two
human gates (`manager_manual_assign`, `underwriter_review_referral`), every
"lead lost" terminal node, and the three end states. Every business
read/write is owned by `lead-domain-service` and reached only through calls
made by `src/orchestrator_app/domain_client.py`.

## Running

```
pip install -r requirements.txt
DRY_RUN=true uvicorn orchestrator_app.main:app --reload
```

With `PYTHONPATH=src` (see `Dockerfile`), or run from `src/`.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DRY_RUN` | `true`/`false`. When true, `DomainClient` returns canned responses instead of calling the network -- no live `lead-domain-service` needed. |
| `DATABASE_URL` | Unused; left blank so run state stays in-memory (see `state.RunRepository`). |
| `LEAD_DOMAIN_SERVICE_URL` | Base URL for the `lead-domain-service` dependency. |
| `DOMAIN_CLIENT_TIMEOUT_SECONDS` / `DOMAIN_CLIENT_MAX_RETRIES` / `DOMAIN_CLIENT_BACKOFF_BASE_SECONDS` | Retry/backoff policy applied to every domain call. |

## HTTP surface

- `GET /health` — `{"status": "ok"}`.
- `POST /runs` — trigger a new run. Body: `{"run_type": "lead"|"agent_management"|"reassignment"|"access_report", ...}`.
  Invokes the compiled graph immediately; returns the run's status after it
  runs to its first halt (a human gate or a terminal node).
- `GET /runs/{run_id}` — run status plus per-step history.
- `GET /runs/{run_id}/events` — Server-Sent Events stream of every
  transition recorded so far, replayed first, then any new ones.
- `POST /runs/{run_id}/steps/manager_manual_assign/approve` — body
  `{"agent_id": "..."}`. Resumes the Manager Assigns Agent From Queue gate
  (REQ-003). Idempotent.
- `POST /runs/{run_id}/steps/underwriter_review_referral/approve` — body
  `{"decision": "approve"|"approve_with_loading"}`. Resumes the Underwriter
  Decides On Referred Risk gate (REQ-007). Idempotent.
- `POST /runs/{run_id}/steps/underwriter_review_referral/reject` — rejects
  the referral; the lead is set Lost with reason "Underwriter declined".
  Idempotent.

## Event format (SSE)

Each event is `data: {"run_id", "step_id", "status", "detail"}\n\n`. A late
subscriber receives every step recorded so far before any live ones.

## Graph

`src/orchestrator_app/graph.py` compiles all 34 nodes from the approved
process model with an in-memory `MemorySaver` checkpointer and
`interrupt_before` on the two human gates, so a run halts there until its
resume/reject endpoint updates state and re-invokes the graph with the same
`thread_id` (the run id). `src/orchestrator_app/nodes.py` implements each
node and the pure decision function used for its conditional edges.

## Known gaps

See `GAPS.json` for every place the frozen contract did not give a concrete
method/path/field and what this service assumed instead.
