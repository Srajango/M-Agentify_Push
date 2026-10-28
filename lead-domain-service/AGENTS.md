---

## Service: lead-domain-service

- kind: backend
- title: Lead & Policy Domain Service
- origin: new
- tech_stack: language=python, framework=fastapi
- plan_status: approved
- assigned stack skill(s): `stack.python-fastapi` (`.opencode/skills/stack-python-fastapi/SKILL.md`), `stack.python-contracts` (`.opencode/skills/stack-python-contracts/SKILL.md`) — open the path in brackets for the FULL body; the
  non-negotiable subset is inlined below so you cannot miss it

## Hard rules from your assigned skills — these are NOT optional reading

## Code Quality Standards (NON-NEGOTIABLE)
- Every function signature MUST declare types for arguments and return values- All endpoints must validate input at the boundary- Use domain exceptions (not bare except/throw)- Test EVERY path: happy path + validation errors + business errors- If a field is not in /repo facts, declare it as a gap in GAPS.json


### From `stack.python-fastapi`
## Non-negotiable rules — the build harness checks each of these

1. **Ship a runnable `tests/` suite.** The platform installs your declared deps and RUNS pytest — a
   failing test, a suite that collects nothing, and a suite where every test is skipped are all gate
   failures, not warnings.
2. **Declare the toolchain in the INSTALLED manifest** (`requirements.txt` or a `test` extra):
   `pytest`, `pytest-asyncio`, `pytest-mock`, and `respx` only with `httpx` / `responses` only with
   `requests`. A mock library that does not match your HTTP client intercepts nothing, and the gate
   reports that as `mock_library_mismatch`.
3. **Set `[tool.pytest.ini_options] asyncio_mode = "auto"`.** Without it every async test is
   silently skipped.
4. **Tests import the same module tree the Dockerfile CMD runs.** `from main import app` when CMD
   targets `src.package.main:app` is a `test_import_mismatch`, not a style choice.
5. **DRY_RUN switches ONE transport seam, never your business logic.** At least one test per
   dependency client must run with `DRY_RUN=false` against a stubbed transport. Never pin `DRY_RUN`
   at module scope or in an autouse fixture.
6. **Exactly one canonical tree** under `services/<service_key>/` — one `app = FastAPI()`, no orphan
   modules at the clone root, no duplicate `src/`.

### From `stack.python-contracts`
## Non-negotiable rules — verify each one before you stop

1. **Every function you define is called, or deleted.** Dead code reads to a reviewer as a shipped
   capability.
2. **An assertion that cannot fail is not a test.** Never widen an assertion, `skip`, `xfail`, or
   delete a test to make a suite pass over a defect you already found — fix the code, or declare it
   in `GAPS.json` with `"severity": "blocking"` and leave the strict assertion failing.
3. **Patch where the name is looked up, not where it is defined** — and a function-local import
   leaves no module-scope attribute to patch.
4. **Never fabricate a value** to fill a gap (a templated email, a hardcoded account number, a
   `'TODO'` literal) — the platform's fabrication scanner treats it as a gating blocker.
5. **The service must import, and its test suite must actually pass** — the platform installs your
   declared dependencies and runs `pytest` for real.
6. **Never pin exact 2024 langchain/langgraph/pydantic versions** (`langgraph==0.2.0`,
   `langchain-core==0.2.38`, `pydantic==2.5.0`). Use the floors `langgraph>=0.2.60`,
   `langchain-core>=0.3.0`, `langsmith>=0.3.45`, `pydantic>=2`. Exact old pins fail `pip install`
   on Python 3.12.4+ (`ResolutionImpossible`).

## Workspace Boundaries (CRITICAL)

All commands MUST respect workspace and service boundaries. This prevents permission escalation errors that block builds.

### Command Constraints

**DO use these patterns:**
- `find .` or `find ./` (search current directory)
- `grep -r . ` (search current workspace)
- `grep -r . services/lead-domain-service/` (search own service)
- `which python3` (discover interpreter)
- `python3 --version` (check version)
- `pip list` (check installed packages)
- `python3 -c "import pkg; print(pkg.__version__)"` (version probe)
- `rm -rf .coverage .pytest_cache` (cleanup with relative paths)
- `python3 -m shutil.rmtree('.coverage')` (Python-based cleanup)

**DO NOT use these patterns:**
- `find /` (system-wide search - will escalate)
- `grep -r ... /` (system-wide grep - will escalate)
- `ls -la /usr/bin/python*` (system discovery - will escalate)
- `find / -iname "*.whl"` (system-wide package search - will escalate)
- `sudo` commands (privilege escalation - will escalate)
- `chmod` commands (permission changes - will escalate)
- `git push` (remote operations - will escalate)
- Paths starting with `/` are escalation risks unless read-only discovery

### Why This Matters

The permission system enforces workspace isolation for safety. System-wide searches trigger security reviews that block your build. Use scoped alternatives:

| Task | Right Way | Wrong Way |
|------|-----------|-----------|
| Find Python | `which python3` | `find / -iname "python3*"` |
| Check package | `pip list | grep pkg` | `find / -iname "*pkg*"` |
| Cleanup | `rm -rf .coverage` | System-wide cleanup |
| Find code | `grep -r anchor .` | `grep -r anchor /` |
| Search service | `find services/lead-domain-service/` | `find / ...` |

### Reference

- Workspace root: `/work/` (mounted at `./`)
- Service directory: `/work/services/lead-domain-service/` (accessed as `./services/lead-domain-service/`)
- Read-only reference: `/repo/` (if applicable)
- Scratch space: `/tmp/` (temporary files only)

Never reference absolute paths like `/work`, `/repo`, or `/` in commands. Use relative paths (`.` or `./`) within your service directory.


## Reviewer change request (REWORK — modify the EXISTING code in `./services/lead-domain-service/`, do not rebuild from scratch)
### Reviewer note for `lead-domain-service`
add a postgres driver such as psycopg[binary] and rebuild the service

## Contract slice (FROZEN v3, hash `sha256:7b8c861e0e8c69d28d234e872c03e7601f41dc6b2c12a6047cb9bdc067a3d460`)
This is the authoritative boundary of this service. Implement every operation in `service.provides` exactly (method, path, fields, errors, idempotency key); call every entry in `consumed` and read only the fields listed in `service.consumes[].fields_used`; honour `failure_policy` timeouts and retries on those calls.

```json
{
 "consumed": {
  "ev_2a8f6dc208ca3c2b": {
   "baseline": false,
   "derived_from": [
    {
     "kind": "edge",
     "ref": "start->role_based_access_control"
    }
   ],
   "name": "",
   "op_id": "ev_2a8f6dc208ca3c2b",
   "payload": {},
   "style": "event"
  },
  "ev_8cd49554c82e88ee": {
   "baseline": false,
   "derived_from": [
    {
     "kind": "edge",
     "ref": "start->register_lead"
    }
   ],
   "name": "",
   "op_id": "ev_8cd49554c82e88ee",
   "payload": {},
   "style": "event"
  },
  "ev_c6f4edb1379eafec": {
   "baseline": false,
   "derived_from": [
    {
     "kind": "edge",
     "ref": "start->manager_reassign_lead"
    }
   ],
   "name": "",
   "op_id": "ev_c6f4edb1379eafec",
   "payload": {},
   "style": "event"
  },
  "ev_e987c924edfd1f27": {
   "baseline": false,
   "derived_from": [
    {
     "kind": "edge",
     "ref": "start->manage_agent_records"
    }
   ],
   "name": "",
   "op_id": "ev_e987c924edfd1f27",
   "payload": {},
   "style": "event"
  }
 },
 "consumed_owner": {
  "ev_2a8f6dc208ca3c2b": "svc_8118635b113f4724ad87",
  "ev_8cd49554c82e88ee": "svc_8118635b113f4724ad87",
  "ev_c6f4edb1379eafec": "svc_8118635b113f4724ad87",
  "ev_e987c924edfd1f27": "svc_8118635b113f4724ad87"
 },
 "contract_version": 3,
 "failure_policy": [
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "register_lead",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "auto_rate_quote",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "auto_assign_agent",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "capture_risk_data",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "auto_screen_appetite",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "client_decision_wait",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "manage_agent_records",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "validate_bind_inputs",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "bind_and_issue_policy",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "manager_reassign_lead",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "record_contact_activity",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "compute_counts_conversion",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "role_based_access_control",
   "retries": 3,
   "timeout_s": 120
  },
  {
   "backoff": "exponential",
   "defaulted": true,
   "node_key": "record_underwriter_outcome",
   "retries": 3,
   "timeout_s": 120
  }
 ],
 "human_gates": [],
 "rule_waivers": [],
 "service": {
  "consumes": [
   {
    "fields_used": [],
    "op_id": "ev_8cd49554c82e88ee"
   },
   {
    "fields_used": [],
    "op_id": "ev_e987c924edfd1f27"
   },
   {
    "fields_used": [],
    "op_id": "ev_c6f4edb1379eafec"
   },
   {
    "fields_used": [],
    "op_id": "ev_2a8f6dc208ca3c2b"
   }
  ],
  "key": "lead-domain-service",
  "kind": "backend",
  "origin": "new",
  "owns_entities": {
   "Activity": {
    "baseline": false,
    "fields": {}
   },
   "Agent": {
    "baseline": false,
    "fields": {}
   },
   "Lead": {
    "baseline": false,
    "fields": {}
   },
   "Policy": {
    "baseline": false,
    "fields": {}
   },
   "Quote": {
    "baseline": false,
    "fields": {}
   },
   "Risk": {
    "baseline": false,
    "fields": {}
   }
  },
  "owns_nodes": [
   "register_lead",
   "auto_assign_agent",
   "manage_agent_records",
   "capture_risk_data",
   "auto_screen_appetite",
   "record_underwriter_outcome",
   "auto_rate_quote",
   "record_contact_activity",
   "client_decision_wait",
   "validate_bind_inputs",
   "bind_and_issue_policy",
   "manager_reassign_lead",
   "role_based_access_control",
   "compute_counts_conversion"
  ],
  "owns_requirements": [
   "REQ-001",
   "REQ-002",
   "REQ-004",
   "REQ-005",
   "REQ-006",
   "REQ-008",
   "REQ-009",
   "REQ-010",
   "REQ-011",
   "REQ-012",
   "REQ-013",
   "REQ-014",
   "REQ-015",
   "REQ-016",
   "REQ-017",
   "REQ-018"
  ],
  "provides": [
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "check_duplicate->auto_assign_agent"
     }
    ],
    "entity": "Lead",
    "errors": [],
    "kind": "command",
    "name": "",
    "op_id": "op_e068c9371edb960b",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "check_agent_available->capture_risk_data"
     }
    ],
    "entity": "Lead",
    "errors": [],
    "kind": "command",
    "name": "",
    "op_id": "op_09da3b189916ddf1",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "manager_manual_assign->capture_risk_data"
     }
    ],
    "entity": "Lead",
    "errors": [],
    "kind": "command",
    "name": "",
    "op_id": "op_7da1e98a2662abb1",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "check_risk_complete->capture_risk_data"
     }
    ],
    "entity": "Lead",
    "errors": [],
    "kind": "command",
    "name": "",
    "op_id": "op_4cfe5e72a9e3ac12",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "check_risk_complete->auto_screen_appetite"
     }
    ],
    "entity": "Risk",
    "errors": [],
    "kind": "command",
    "name": "",
    "op_id": "op_9d2a3f9c0f8666c3",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "check_screen_outcome_refer->auto_rate_quote"
     }
    ],
    "entity": "Quote",
    "errors": [],
    "kind": "command",
    "name": "",
    "op_id": "op_ad62bb70c888681f",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "check_underwriter_decision->record_underwriter_outcome"
     }
    ],
    "entity": "Risk",
    "errors": [],
    "kind": "command",
    "name": "",
    "op_id": "op_c077bc2e72e5ccaf",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "agent_rerate_decision->capture_risk_data"
     }
    ],
    "entity": "Lead",
    "errors": [],
    "kind": "command",
    "name": "",
    "op_id": "op_7bbb0af5636162bb",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "agent_rerate_decision->client_decision_wait"
     }
    ],
    "entity": "Quote",
    "errors": [],
    "kind": "query",
    "name": "",
    "op_id": "op_071073fcac0c7274",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "check_client_outcome_accept->validate_bind_inputs"
     }
    ],
    "entity": "Quote",
    "errors": [],
    "kind": "query",
    "name": "",
    "op_id": "op_04ae95f667cdc9fb",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "entity_read",
      "ref": "Lead"
     }
    ],
    "entity": "Lead",
    "errors": [],
    "kind": "query",
    "name": "",
    "op_id": "op_bc60747eec921ea0",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "entity_read",
      "ref": "Agent"
     }
    ],
    "entity": "Agent",
    "errors": [],
    "kind": "query",
    "name": "",
    "op_id": "op_ac2705604a6aa3f8",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "entity_read",
      "ref": "Risk"
     }
    ],
    "entity": "Risk",
    "errors": [],
    "kind": "query",
    "name": "",
    "op_id": "op_e12584afb808ad57",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "entity_read",
      "ref": "Quote"
     }
    ],
    "entity": "Quote",
    "errors": [],
    "kind": "query",
    "name": "",
    "op_id": "op_4879b34b0dd377de",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "health",
      "ref": "svc_9fc65e7776e44c85b429"
     }
    ],
    "errors": [],
    "kind": "health",
    "method": "GET",
    "name": "health",
    "op_id": "op_d05607ba2d958de5",
    "path": "/health",
    "request": {},
    "response": {
     "status": {
      "required": true,
      "type": "string"
     }
    },
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "ccr",
      "ref": "7359b231-474e-4af5-aa25-d4b2ef2626ca"
     }
    ],
    "errors": [],
    "kind": "command",
    "method": "POST",
    "name": "upsert_agent_record",
    "op_id": "op_9fcce42948fc43c0",
    "path": "/agents",
    "request": {
     "active": {
      "required": true,
      "type": "bool"
     },
     "agent_id": {
      "required": false,
      "type": "uuid"
     },
     "city": {
      "required": true,
      "type": "string"
     },
     "name": {
      "required": true,
      "type": "string"
     }
    },
    "response": {
     "active": {
      "required": true,
      "type": "bool"
     },
     "agent_id": {
      "required": true,
      "type": "uuid"
     },
     "city": {
      "required": true,
      "type": "string"
     },
     "name": {
      "required": true,
      "type": "string"
     }
    },
    "style": "sync"
   }
  ],
  "publishes": [
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "register_lead->check_duplicate"
     }
    ],
    "name": "",
    "op_id": "ev_9647b4fa974052af",
    "payload": {},
    "style": "event"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "manage_agent_records->end_access_counts"
     }
    ],
    "name": "",
    "op_id": "ev_df35d0b35c6d7375",
    "payload": {},
    "style": "event"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "manager_reassign_lead->end_reassign"
     }
    ],
    "name": "",
    "op_id": "ev_ae38e9e0744f83d2",
    "payload": {},
    "style": "event"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "edge",
      "ref": "compute_counts_conversion->end_access_counts"
     }
    ],
    "name": "",
    "op_id": "ev_603d5a9dc674d79a",
    "payload": {},
    "style": "event"
   }
  ],
  "service_uid": "svc_9fc65e7776e44c85b429"
 },
 "status_vocabularies": {}
}
```

## Your API contract (implement these endpoints EXACTLY — this is what gets frozen and published, and what your consumers build against)
A path parameter may be written `{name}`, `<converter:name>`, or `:name`. Those are the same segment. Declare it with your stack's own syntax.
- `GET /health` — health
- `POST /agents` — upsert_agent_record

## Calls you MUST make (declared in your approved plan)
- `EVENT ` on `orchestrator`  [event]
- `EVENT ` on `orchestrator`  [event]
- `EVENT ` on `orchestrator`  [event]
- `EVENT ` on `orchestrator`  [event]
A `webhook` entry means the dependency calls YOU back — implement and publish the callback endpoint named above. Replacing it with a poll is a different system, not an implementation detail. A field listed under a call was VERIFIED to exist at Gate 3 — read it from the response; do not fabricate a substitute if it looks absent.

## Ordered tasks
1. Scaffold the FastAPI service, database models and health check — Create the FastAPI application, PostgreSQL connection, SQLAlchemy models and Alembic migrations for the Lead, Risk, Agent, Quote, Policy and Activity tables, and the health endpoint. [Done when: GET /health returns 200 with a status field
running the migrations creates the leads, risks, agents, quotes, policies and activities tables]
2. Lead registration, duplicate blocking, and agent assignment — Build the lead registration endpoint with the sequential open-lead duplicate check, the round-robin agent assignment endpoint (auto and manager-chosen), the lead reassignment endpoint for managers, and the agent roster lookup and create/update endpoint used by both. [Done when: registering a lead with a mobile number and vehicle registration number already open on another lead is refused and no second lead is created
registering a new combination succeeds with status New
assigning a lead whose city has an active agent succeeds automatically and never leaves the lead unassigned
reassigning a Converted or Lost lead is rejected
reassigning an open lead to a different active agent keeps its activities and status unchanged
creating an agent record and then deactivating it removes it from the active roster used by round-robin assignment]
3. Risk capture, appetite screening and underwriting outcome — Build the risk data submission endpoint that keeps status at Capture until every required fact is present, the ordered first-match-wins appetite screening endpoint that sets the lead to Lost on a decline, and the endpoint that records the underwriter's approve, approve-with-loading or decline outcome, setting the lead to Lost with reason 'Underwriter declined' on decline. [Done when: submitting incomplete risk data keeps the lead in Capture status and lists the missing facts
submitting complete data marks the risk complete
screening a risk that matches an ordered decline rule sets the lead to Lost with that reason and stops checking further rules
screening a risk that matches no decline rule but a refer rule marks it referred without changing the lead's status
recording an underwriter decline sets the lead to Lost with reason 'Underwriter declined'
recording an underwriter approve or approve-with-loading stores it as the latest approved risk]
4. Rate card engine and versioned quoting — Build the quote rating endpoint that reads the latest approved risk, applies the agency rate card formula for Third Party or Comprehensive coverage including no-claim bonus and loading, rounds the total to the nearest rupee, stores a new quote version with its breakdown, rated time and a seven-day expiry, marks any prior version replaced, and sets the lead to Quoted. [Done when: rating a Comprehensive risk computes own damage as IDV times 0.035 times one minus the no-claim fraction, adds the third-party premium and loading, and rounds the stored total to the nearest rupee
rating the same lead again creates a new higher-numbered quote version and marks the previous version replaced
only the newest quote version can later be accepted]
5. Agent contact activities and client quote decision — Build the append-only contact activity endpoint recording date and time, agent, channel, outcome, note and optional next follow-up date, and the client quote decision endpoint that records a decline with its reason and sets the lead to Lost, or reports the current quote status for an acceptance to proceed to bind. Include the internal check that automatically sets the lead to Lost with reason 'Quote expired' once the seventh day ends with no acceptance. [Done when: recording a contact activity appends a new row and no endpoint can edit or delete it
declining a quote with a reason of price, bought elsewhere, or not interested sets the lead to Lost with that reason
a quote whose seventh day has ended with no acceptance is automatically set to Lost with reason 'Quote expired' without any human choosing it]
6. Bind validation and policy issuance — Build the bind-input validation endpoint that checks the effective date is on or after today and on or before the quote's expiry date, and that the collected amount equals the latest quote version's total, and the bind endpoint that issues a unique policy number in the form PC-{calendar year}-{six digits}, stores the policy snapshot from the accepted quote version, and sets the lead to Converted. [Done when: binding with an effective date before today or after the quote expiry is rejected with no policy created
binding with a collected amount different from the latest quote total is rejected with no policy created
binding with valid inputs issues a unique policy number in the form PC-{calendar year}-{six digits}
a successful bind stores the coverage, IDV, premium breakdown, no-claim bonus, loading and effective date, and sets the lead to Converted]
7. Role-based visibility and agency reporting counts — Build the role-scoped lead listing endpoint so an agent sees only their own leads, an underwriter sees the referral queue, and a manager sees every lead, and the counts endpoint that computes, for each agent and for the agency, leads assigned, leads still open, clients converted, leads lost, and conversion rate as converted divided by assigned, all read live from the lead records. [Done when: an agent's request returns only leads assigned to that agent
a manager's request returns every lead
the conversion rate returned for an agent equals that agent's converted lead count divided by their assigned lead count, computed live from the lead table and never a hand-entered value]
8. Publish domain events, consume workflow events, and end-to-end tests — Publish a lead-registered event, a lead-status-changed event, a quote-issued event and a policy-issued event at the points described above. Subscribe to the four workflow events from the gate-owning service (manual assignment made, underwriter decision made, client accepted, client declined) and log them for audit correlation. Add integration tests covering the full intake-to-bind path and the duplicate, decline, referral, re-rate, decline-by-client and expiry branches. [Done when: each of the four domain events is published exactly once at its trigger point in a dedicated test
subscribing to the four workflow events logs them for audit correlation without raising on duplicate delivery
the integration test suite exercises registration, duplicate blocking, assignment, capture, screening decline, referral approval, rating, re-rating, client decline, quote expiry, and bind]

## Requirements you own — every one needs code, and you must prove it
- [REQ-001] (must) Register new lead with intake fields: customer's name, mobile number, email, city, source, and the product Private Car. Status becomes New.
- [REQ-002] (must) Block duplicate open lead by mobile and vehicle registration number via a simple sequential check; concurrent race conditions are out of scope.
- [REQ-004] (must) Capture complete risk data before proceeding; status becomes Capture until every required fact is present, and the case does not continue while a required fact is missing. If the lead remains in Capture status indefinitely (missing data for an extended period), no automatic action is taken; the lead remains in Capture until the agent completes it.
- [REQ-005] (must) Automatically screen appetite with ordered decline/refer rules, first match wins, with no added human review step in the chain.
- [REQ-006] (must) Decline sets lead Lost and ends case; a lost lead is not a conversion.
- [REQ-008] (must) Underwriter decline sets lead Lost with reason 'Underwriter declined' and the case ends.
- [REQ-009] (must) Automatically rate the latest approved risk from the agency rate card and store a new quote version; the quote records the breakdown, the time, and an expiry at the end of the seventh day. Status becomes Quoted. Only this rate card is used. Rating runs fully automatically with no added review step.
- [REQ-010] (must) Apply rate card formula for premium calculation per coverage type (Third Party / Comprehensive), including no-claim bonus and loading rules, rounded to the nearest rupee.
- [REQ-011] (must) Record agent contact activities on lead: date and time, agent, channel (call, meeting, or WhatsApp), outcome (no answer, interested, follow-up booked, or not interested), a note, and an optional next follow-up date. Activities are never edited or deleted.
- [REQ-012] (must) Allow re-rating with versioned quotes before acceptance; only the latest version can be accepted; a version that was declined, expired, or replaced cannot be bound.
- [REQ-013] (must) Handle client accept, decline, or quote expiry: acceptance moves case to bind; decline records a reason (price, bought elsewhere, or not interested) and sets lead Lost; the seventh day ending with no acceptance automatically sets the lead to Lost with reason 'Quote expired' with no human choosing this.
- [REQ-014] (must) Bind acceptance and issue unique policy number in the form PC-{calendar year}-{six digits}, and store the policy from that quote version: coverage, IDV, premium breakdown, no-claim bonus, loading, and effective date. The lead status becomes Converted.
- [REQ-015] (must) Validate effective date and collected amount at bind: effective date on or after today and on or before the quote expiry date; amount collected equals the quote total of the latest version.
- [REQ-016] (must) Manager reassigns an open lead (not Converted and not Lost) to a different active agent; past activities stay on the lead; the new agent owns the next actions; status does not change. A Converted or Lost lead cannot be reassigned.
- [REQ-017] (must) Enforce role-based visibility and actions: an agent sees only their own leads, the risk form, the quote, and the activity timeline, and can record a contact, an acceptance, or a client decline; an underwriter sees the referral queue and decides approve, approve with loading, or decline; a manager sees every lead, reassigns an open lead, and sees the counts.
- [REQ-018] (must) Compute counts and conversion rate from records: for each agent and for the agency, leads assigned, leads still open, clients converted, leads lost, and conversion rate equal to converted divided by assigned, read from leads and never entered by hand.

These are assigned to THIS service; no other worker is implementing them. A requirement is satisfied by CODE THAT RUNS — not by a database column named after it and never read, and not by one of two required channels.
Before you finish, write `ATTESTATION.json` at your service root: a JSON object
`{"version": 1, "service_key": "...", "requirements": [...]}` with one entry per requirement above, shaped
`{"req_key", "status": "implemented"|"partial"|"not_implemented", "file", "line", "symbol", "test", "note"}`.
`file`/`symbol` must name code you actually wrote that ENFORCES the rule (a schema column or a config key is not evidence); `test` is the test that fails if the requirement is removed. Anything you could not implement is `not_implemented` with a `note` — and also a `GAPS.json` entry. Declaring a gap is a finding for a human to review; a false claim is a defect the platform will catch, since every field here is checked against your code.

## Process flow you own — from the APPROVED process model (this is the control flow, not background reading)
Steps:
- `register_lead [automated]` Register New Lead
    Registers lead with customer's name, mobile number, email, city, source, and product Private Car. Status becomes New.
- `auto_assign_agent [automated]` Auto-Assign Agent By Round-Robin
    Automatically assigns lead via round-robin among active agents serving the lead's city.
- `manage_agent_records [automated]` Maintain Agent Records
    Manager maintains agent records, their city coverage, and active/inactive status within the application.
- `capture_risk_data [automated]` Capture Risk Data
    Status becomes Capture until every required risk fact is present. Case does not continue while a required fact is missing. Lead remains in Capture indefinitely until the agent completes it.
- `auto_screen_appetite [automated]` Auto-Screen Appetite
    Automatically screens appetite with ordered decline/refer rules; first match wins; no added human review step.
- `record_underwriter_outcome [automated]` Record Underwriter Approval Outcome
    Records the underwriter's Approve or Approve with loading decision on the risk as the latest approved risk.
- `auto_rate_quote [automated]` Auto-Rate Latest Approved Risk
    Automatically rates the latest approved risk from the agency rate card and stores a new quote version with breakdown, time, and expiry at end of seventh day. Status becomes Quoted. Only this rate card is used. Fully automatic with no added review step.
- `record_contact_activity [automated]` Record Agent Contact Activity
    Records agent contact activities on the lead: date/time, agent, channel, outcome, note, optional next follow-up date. Activities are never edited or deleted.
- `client_decision_wait [automated]` Wait For Client Accept, Decline, Or Expiry
    Waits for client to accept or decline the quote, or for the seventh day to end with no acceptance.
- `validate_bind_inputs [automated]` Validate Effective Date And Collected Amount
    Validates effective date is on or after today and on or before the quote expiry date; amount collected equals the quote total of the latest version.
- `bind_and_issue_policy [automated]` Bind Acceptance And Issue Policy
    Issues unique policy number PC-{calendar year}-{six digits} and stores the policy from that quote version: coverage, IDV, premium breakdown, no-claim bonus, loading, and effective date. Lead status becomes Converted.
- `manager_reassign_lead [automated]` Manager Reassigns Open Lead
    Manager reassigns an open lead (not Converted and not Lost) to a different active agent. Past activities stay on the lead. The new agent owns the next actions. Status does not change.
- `role_based_access_control [automated]` Enforce Role-Based Visibility And Actions
    Enforces that an agent sees only their own leads, risk form, quote, and activity timeline and can record contact, acceptance, or decline; underwriter sees referral queue; manager sees every lead, reassigns, and sees counts.
- `compute_counts_conversion [automated]` Compute Counts And Conversion Rate
    Computes, for each agent and the agency, leads assigned, leads still open, clients converted, leads lost, and conversion rate equal to converted divided by assigned, read from leads and never entered by hand.

Transitions:
- `record_underwriter_outcome -> auto_rate_quote`
- `auto_rate_quote -> record_contact_activity`
- `validate_bind_inputs -> bind_and_issue_policy`
- `role_based_access_control -> compute_counts_conversion`

Entry: `register_lead`, `auto_assign_agent`, `manage_agent_records`, `capture_risk_data`, `auto_screen_appetite`, `record_underwriter_outcome`, `client_decision_wait`, `validate_bind_inputs`, `manager_reassign_lead`, `role_based_access_control`.  Terminal: (none).

Build EXACTLY this graph. Every step above is a node in your compiled runtime graph and every transition is an edge in it. A transition carrying a condition is a CONDITIONAL edge, and two conditions leaving one step MUST route to different targets — mapping both to the same next step deletes the business rule the branch came from. Writing a handler function for a step and not adding that step to the compiled graph does NOT implement it: the function is unreachable and the run flows past it. Before you finish, walk this list and confirm every step and every transition is present in the compiled graph.

## Tests you MUST write (the platform INSTALLS your deps and ACTUALLY RUNS these with pytest — a failing test blocks Gate 4, not just a collection error)
- Declare the test toolchain in your INSTALLED manifest (requirements.txt or a `test` extra) and set `[tool.pytest.ini_options] asyncio_mode = "auto"`: pytest, pytest-asyncio, pytest-mock, and whichever of respx/responses matches your HTTP client (respx only intercepts httpx; responses only intercepts requests).
- Put every test under `tests/`. Most tests run under `DRY_RUN=true` with NO real network / DB / secrets — fake those at the boundary. But DRY_RUN stubs ONE seam, not your business logic: at least one test per dependency client MUST run with `DRY_RUN=false` against the stubbed transport and assert the real request URL/method/body/auth header — a suite that is 100% DRY_RUN has verified nothing about your actual integration code. Never pin `DRY_RUN` at module scope or in an autouse fixture; set it per-test only.
- Settings must bind env via `Field(alias="DRY_RUN")` / `Field(alias="DATABASE_URL")` (and the same pattern for every other env key). Do not rely on a second lowercase `dry_run` env var — the harness emits `DRY_RUN` only.
- `.env.example` must not pin live infrastructure URLs. Leave `DATABASE_URL` blank or unset so the harness and local loops use in-memory storage/checkpointing.
- Never return empty `{}` from a LangGraph node that runs after a writer on a structural edge; re-emit the prior `result`/`error` (explicit passthrough) or return `None` only when no prior channel write must be preserved. An empty update after a writer raises `InvalidUpdateError` and aborts the request.
- Tests MUST import the same module tree the Dockerfile CMD runs; importing orphan root files (e.g. `from main import app` when CMD is `src.package.main:app`) is a gate failure.
- Do NOT create a second implementation at the clone root or a parallel package name — exactly ONE canonical tree under `./services/lead-domain-service/`.
- Use src-layout: application code under `src/<package>/`, never `main.py` or `graph.py` at the service root (the layout gate blocks flat root trees).
- An "imports cleanly" test (importing the app/graph must not raise) and, for HTTP services, a `/health` test.
- One test per endpoint in "Your API contract" above: call it and assert the status code plus the `response_example` shape.
- Before you finish, verify every module and every function you created is imported and reachable from the entrypoint. A function nothing calls is dead code to delete, not a capability you shipped.

## Approved plan
## Build order

1. **Scaffold the FastAPI service, database models and health check** — stand up the app, the PostgreSQL models for Lead, Risk, Agent, Quote, Policy and Activity, their Alembic migrations, and the health check endpoint.
2. **Lead registration, duplicate blocking, and agent assignment** — the endpoint to register a new lead with its intake fields and product Private Car (status New) after a sequential check blocks a duplicate open lead by mobile number and vehicle registration number; the round-robin auto-assignment endpoint among active agents in the lead's city (falling back to a manager's manual pick when none is available, with the lead never left unassigned or double-assigned); the manager reassignment endpoint for an open lead to a different active agent (status and activity history unchanged, Converted/Lost leads rejected); and the agent roster endpoints — a lookup by city and active status, and a create/update endpoint for an agent's name, city coverage and active flag.
3. **Risk capture, appetite screening and underwriting outcome** — the risk submission endpoint that holds the lead in Capture status until every required fact is present; the ordered, first-match-wins appetite screening endpoint that sets the lead to Lost on a decline match; and the endpoint recording the underwriter's approve, approve-with-loading, or decline outcome (decline sets the lead to Lost with reason "Underwriter declined").
4. **Rate card engine and versioned quoting** — rates the latest approved risk against the agency rate card (own damage, third-party premium, no-claim bonus and loading, rounded to the nearest rupee for both Third Party and Comprehensive coverage), stores a new quote version with its breakdown, timestamp and seven-day expiry, marks any earlier version replaced on a re-rate, and sets the lead to Quoted.
5. **Agent contact activities and client quote decision** — an append-only endpoint for logging a contact (date/time, agent, channel, outcome, note, optional follow-up date) that can never be edited or deleted; and the client decision endpoint that records a decline with its reason (price, bought elsewhere, or not interested) and sets the lead to Lost, reports quote status for the acceptance path, and applies the automatic "Quote expired" Lost outcome once the seventh day passes with no acceptance.
6. **Bind validation and policy issuance** — validates the effective date (on or after today, on or before the quote's expiry) and the collected amount (equal to the latest quote's total) before binding; then issues a unique policy number in the form PC-{calendar year}-{six digits}, stores the policy snapshot (coverage, IDV, premium breakdown, no-claim bonus, loading, effective date) from the accepted quote version, and sets the lead to Converted.
7. **Role-based visibility and agency reporting counts** — a role-scoped lead listing (an agent sees only their own leads, an underwriter sees the referral queue, a manager sees every lead) and a counts endpoint computing, for each agent and the agency, leads assigned, still open, converted, lost, and the conversion rate (converted divided by assigned), always read live from lead records.
8. **Publish domain events, consume workflow events, and end-to-end tests** — publish a lead-registered event, a lead-status-changed event, a quote-issued event and a policy-issued event at their trigger points; subscribe to the four workflow events from the gate-owning service (manual assignment made, underwriter decision made, client accepted, client declined) and log them for audit correlation; and add integration tests covering the full intake-to-bind path plus the duplicate, decline, referral, re-rate, client-decline and expiry branches.


## Workspace map
No prior graph brief yet (greenfield). Prefer the `codegraph` MCP tool before broad greps; stay inside your `services/<service_key>/` tree.

## Code navigation tools
Before exploratory file reads or greps, query the local MCP servers:
- `codegraph` — indexed symbol/call graph for THIS worktree (auto-sync while you edit)
Use the Workspace map section above as the cheap always-on overview.

The API contract blocks above are AUTHORITATIVE: implement your own surface exactly as listed, call each
dependency ONLY at the endpoints in its FROZEN block, and never call or expose an endpoint that appears
only in the prose plan. Declare every import in your dependency manifest — the service must import/compile
cleanly, because the platform runs an import/compile smoke check before this work is accepted.

The process-flow and human-gate blocks are equally authoritative: a step you did not add to the compiled
graph, a conditional branch whose outcomes share one target, or a gate the run does not halt at is an
unimplemented requirement, not a stylistic difference.

Write code ONLY inside this workspace, only for `lead-domain-service`. Follow the approved plan —
do not expand scope. Prefer small, runnable files over large frameworks.

