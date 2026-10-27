---

## Service: orchestrator

- kind: orchestrator
- title: Lead-to-Policy Orchestrator
- origin: new
- tech_stack: language=python, framework=fastapi-langgraph
- plan_status: approved
- assigned stack skill(s): `stack.python-fastapi-langgraph` (`.opencode/skills/stack-python-fastapi-langgraph/SKILL.md`), `stack.python-contracts` (`.opencode/skills/stack-python-contracts/SKILL.md`) — open the path in brackets for the FULL body; the
  non-negotiable subset is inlined below so you cannot miss it

## Hard rules from your assigned skills — these are NOT optional reading

## Code Quality Standards (NON-NEGOTIABLE)
- Every function signature MUST declare types for arguments and return values- All endpoints must validate input at the boundary- Use domain exceptions (not bare except/throw)- Test EVERY path: happy path + validation errors + business errors- If a field is not in /repo facts, declare it as a gap in GAPS.json


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
- `grep -r . services/orchestrator/` (search own service)
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
| Search service | `find services/orchestrator/` | `find / ...` |

### Reference

- Workspace root: `/work/` (mounted at `./`)
- Service directory: `/work/services/orchestrator/` (accessed as `./services/orchestrator/`)
- Read-only reference: `/repo/` (if applicable)
- Scratch space: `/tmp/` (temporary files only)

Never reference absolute paths like `/work`, `/repo`, or `/` in commands. Use relative paths (`.` or `./`) within your service directory.


## Reviewer change request (REWORK — modify the EXISTING code in `./services/orchestrator/`, do not rebuild from scratch)
This service is failing because of issue 2 attestation(s) do not match the code: REQ-003 names `node_auto_assign_agent, node_check_agent_available, node_manager_manual_assign` in src/orchestrator_app/nodes.py, which is not there; REQ-007 nam. Resolve it during rework.

## Contract slice (FROZEN v3, hash `sha256:7b8c861e0e8c69d28d234e872c03e7601f41dc6b2c12a6047cb9bdc067a3d460`)
This is the authoritative boundary of this service. Implement every operation in `service.provides` exactly (method, path, fields, errors, idempotency key); call every entry in `consumed` and read only the fields listed in `service.consumes[].fields_used`; honour `failure_policy` timeouts and retries on those calls.

```json
{
 "consumed": {
  "ev_603d5a9dc674d79a": {
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
  },
  "ev_9647b4fa974052af": {
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
  "ev_ae38e9e0744f83d2": {
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
  "ev_df35d0b35c6d7375": {
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
  "op_04ae95f667cdc9fb": {
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
  "op_071073fcac0c7274": {
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
  "op_09da3b189916ddf1": {
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
  "op_4879b34b0dd377de": {
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
  "op_4cfe5e72a9e3ac12": {
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
  "op_7bbb0af5636162bb": {
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
  "op_7da1e98a2662abb1": {
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
  "op_9d2a3f9c0f8666c3": {
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
  "op_ac2705604a6aa3f8": {
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
  "op_ad62bb70c888681f": {
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
  "op_bc60747eec921ea0": {
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
  "op_c077bc2e72e5ccaf": {
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
  "op_e068c9371edb960b": {
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
  "op_e12584afb808ad57": {
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
  }
 },
 "consumed_owner": {
  "ev_603d5a9dc674d79a": "svc_9fc65e7776e44c85b429",
  "ev_9647b4fa974052af": "svc_9fc65e7776e44c85b429",
  "ev_ae38e9e0744f83d2": "svc_9fc65e7776e44c85b429",
  "ev_df35d0b35c6d7375": "svc_9fc65e7776e44c85b429",
  "op_04ae95f667cdc9fb": "svc_9fc65e7776e44c85b429",
  "op_071073fcac0c7274": "svc_9fc65e7776e44c85b429",
  "op_09da3b189916ddf1": "svc_9fc65e7776e44c85b429",
  "op_4879b34b0dd377de": "svc_9fc65e7776e44c85b429",
  "op_4cfe5e72a9e3ac12": "svc_9fc65e7776e44c85b429",
  "op_7bbb0af5636162bb": "svc_9fc65e7776e44c85b429",
  "op_7da1e98a2662abb1": "svc_9fc65e7776e44c85b429",
  "op_9d2a3f9c0f8666c3": "svc_9fc65e7776e44c85b429",
  "op_ac2705604a6aa3f8": "svc_9fc65e7776e44c85b429",
  "op_ad62bb70c888681f": "svc_9fc65e7776e44c85b429",
  "op_bc60747eec921ea0": "svc_9fc65e7776e44c85b429",
  "op_c077bc2e72e5ccaf": "svc_9fc65e7776e44c85b429",
  "op_e068c9371edb960b": "svc_9fc65e7776e44c85b429",
  "op_e12584afb808ad57": "svc_9fc65e7776e44c85b429"
 },
 "contract_version": 3,
 "failure_policy": [],
 "human_gates": [
  {
   "node_key": "manager_manual_assign",
   "resume_op_id": "op_ce482f80d0fcea34",
   "ui_service_uid": "svc_992c5968aab6457e8c86"
  },
  {
   "node_key": "underwriter_review_referral",
   "reject_op_id": "op_bc42e7eadaa65523",
   "resume_op_id": "op_e24ddacd8a90f3a1",
   "ui_service_uid": "svc_992c5968aab6457e8c86"
  }
 ],
 "rule_waivers": [],
 "service": {
  "consumes": [
   {
    "fields_used": [],
    "op_id": "ev_9647b4fa974052af"
   },
   {
    "fields_used": [],
    "op_id": "op_e068c9371edb960b"
   },
   {
    "fields_used": [],
    "op_id": "op_09da3b189916ddf1"
   },
   {
    "fields_used": [],
    "op_id": "op_7da1e98a2662abb1"
   },
   {
    "fields_used": [],
    "op_id": "op_4cfe5e72a9e3ac12"
   },
   {
    "fields_used": [],
    "op_id": "op_9d2a3f9c0f8666c3"
   },
   {
    "fields_used": [],
    "op_id": "op_ad62bb70c888681f"
   },
   {
    "fields_used": [],
    "op_id": "op_c077bc2e72e5ccaf"
   },
   {
    "fields_used": [],
    "op_id": "op_7bbb0af5636162bb"
   },
   {
    "fields_used": [],
    "op_id": "op_071073fcac0c7274"
   },
   {
    "fields_used": [],
    "op_id": "op_04ae95f667cdc9fb"
   },
   {
    "fields_used": [],
    "op_id": "ev_df35d0b35c6d7375"
   },
   {
    "fields_used": [],
    "op_id": "ev_ae38e9e0744f83d2"
   },
   {
    "fields_used": [],
    "op_id": "ev_603d5a9dc674d79a"
   },
   {
    "fields_used": [],
    "op_id": "op_bc60747eec921ea0"
   },
   {
    "fields_used": [],
    "op_id": "op_ac2705604a6aa3f8"
   },
   {
    "fields_used": [],
    "op_id": "op_e12584afb808ad57"
   },
   {
    "fields_used": [],
    "op_id": "op_4879b34b0dd377de"
   }
  ],
  "key": "orchestrator",
  "kind": "orchestrator",
  "origin": "new",
  "owns_entities": {},
  "owns_nodes": [
   "start",
   "check_duplicate",
   "duplicate_declined",
   "check_agent_available",
   "manager_manual_assign",
   "check_risk_complete",
   "check_screen_outcome_decline",
   "lead_lost_decline_screen",
   "check_screen_outcome_refer",
   "underwriter_review_referral",
   "check_underwriter_decision",
   "lead_lost_underwriter_decline",
   "agent_rerate_decision",
   "check_client_outcome_accept",
   "check_client_outcome_decline",
   "lead_lost_client_decline",
   "lead_lost_quote_expired",
   "end_converted",
   "end_reassign",
   "end_access_counts"
  ],
  "owns_requirements": [
   "REQ-003",
   "REQ-007"
  ],
  "provides": [
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "human_gate",
      "ref": "manager_manual_assign"
     }
    ],
    "errors": [],
    "kind": "resume",
    "name": "",
    "op_id": "op_ce482f80d0fcea34",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "human_gate",
      "ref": "underwriter_review_referral"
     }
    ],
    "errors": [],
    "kind": "resume",
    "name": "",
    "op_id": "op_e24ddacd8a90f3a1",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "human_gate",
      "ref": "underwriter_review_referral"
     }
    ],
    "errors": [],
    "kind": "reject",
    "name": "",
    "op_id": "op_bc42e7eadaa65523",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "trigger",
      "ref": "trigger"
     }
    ],
    "errors": [],
    "kind": "trigger",
    "name": "",
    "op_id": "op_2e1c5502529ae400",
    "request": {},
    "response": {},
    "style": "sync"
   },
   {
    "baseline": false,
    "derived_from": [
     {
      "kind": "health",
      "ref": "svc_8118635b113f4724ad87"
     }
    ],
    "errors": [],
    "kind": "health",
    "method": "GET",
    "name": "health",
    "op_id": "op_db8d1ee997721bd1",
    "path": "/health",
    "request": {},
    "response": {
     "status": {
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
      "ref": "start->register_lead"
     }
    ],
    "name": "",
    "op_id": "ev_8cd49554c82e88ee",
    "payload": {},
    "style": "event"
   },
   {
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
   },
   {
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
   {
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
   }
  ],
  "service_uid": "svc_8118635b113f4724ad87"
 },
 "status_vocabularies": {}
}
```

## Your API contract (implement these endpoints EXACTLY — this is what gets frozen and published, and what your consumers build against)
A path parameter may be written `{name}`, `<converter:name>`, or `:name`. Those are the same segment. Declare it with your stack's own syntax.
- `GET /health` — health

## Calls you MUST make (declared in your approved plan)
- `EVENT ` on `lead-domain-service`  [event]
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `EVENT ` on `lead-domain-service`  [event]
- `EVENT ` on `lead-domain-service`  [event]
- `EVENT ` on `lead-domain-service`  [event]
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
- `? ?` on `lead-domain-service`
A `webhook` entry means the dependency calls YOU back — implement and publish the callback endpoint named above. Replacing it with a poll is a different system, not an implementation detail. A field listed under a call was VERIFIED to exist at Gate 3 — read it from the response; do not fabricate a substitute if it looks absent.

## Dependency contracts (FROZEN — build against these, never redesign them)
A path parameter may be written `{name}`, `<converter:name>`, or `:name`. Those are the same segment. Call it with your stack's own syntax.
### `lead-domain-service`
- Reference mock (Prism) may be available at http://mock-lead-domain-service:5097 for inspecting example responses — you are NOT required to call it; implement to the contract below.
- `GET /health` — health
- `POST /agents` — upsert_agent_record
## Producer implementation notes (from completed upstream workers — read-only)
Call ONLY these routes (or paths in the FROZEN contract). Do not invent alternate URLs.
### `lead-domain-service` (producer — DONE)
- Boot module (Dockerfile CMD): `lead_domain.main:app`
- Top routes actually generated:
  - `GET /agents`
  - `GET /counts`
  - `GET /health`
  - `GET /leads`
  - `GET /leads/{lead_id}`
  - `GET /leads/{lead_id}/activities`
  - `GET /leads/{lead_id}/quotes`
  - `POST /agents`
  - `POST /leads`
  - `POST /leads/{lead_id}/activities`

## Ordered tasks
1. Scaffold the FastAPI + LangGraph orchestrator service with health check — Create the FastAPI app, LangGraph workflow runner scaffolding, config/env loading, and the health endpoint. Define the run-state model (lead id, current node, pending gate) that the graph will carry through every node. [Done when: GET /health returns {status: 'ok'}
The app boots with an empty/no-op LangGraph graph registered]
2. Build the lead-to-policy workflow graph and its trigger entry point — Implement the LangGraph graph for every node this service owns: start, Open Lead With Same Mobile And Vehicle Reg Exists?, Registration Refused - Duplicate Lead, Active Agent Available In City?, All Required Risk Facts Present?, Appetite Screen Result Is Decline?, Lead Lost - Declined By Screening, Appetite Screen Result Is Refer?, Underwriter Declined Risk?, Lead Lost - Underwriter Declined, Agent Changes Risk And Re-Rates Before Acceptance?, Client Accepted Quote?, Client Declined Quote?, Lead Lost - Client Declined, Lead Lost - Quote Expired, Lead Converted, Reassignment Complete, Access And Reporting Available. The trigger operation starts a new run (main lead pipeline, or the reassignment / access-and-reporting side flows) and advances the graph by calling the backend domain service for every automated business step in between (wired in a later task) and pausing at the two human gates. [Done when: A new-lead run walks start through duplicate check, assignment, capture, screening, rating, activity/re-rate loop and client decision in the exact branching of the process flow, reaching Lead Converted, a Lost terminal node, or a paused human gate as appropriate
A reassignment run reaches Reassignment Complete and an access-and-reporting run reaches Access And Reporting Available]
3. Implement the Manager Assigns Agent From Queue human gate — When Active Agent Available In City? is no, pause the run at the manager_manual_assign gate with no timeout and no auto-escalation. The manager picks an active agent from their own queue in the UI service; calling the gate's resume operation with the chosen agent assigns the lead to exactly one agent and resumes the run into risk capture. [Done when: A run that reaches this gate stays paused indefinitely until the resume operation is called
Calling the resume operation with one active agent assigns the lead to that agent exactly once and continues to Capture Risk Data
The lead is never left unassigned and never assigned to two agents]
4. Implement the Underwriter Decides On Referred Risk human gate — When Appetite Screen Result Is Refer? is yes, pause the run at underwriter_review_referral with no timeout and no auto-escalation. The underwriter checks their own referral queue in the UI service. Calling the gate's resume operation with Approve or Approve with loading records the approved risk outcome and continues to Auto-Rate Latest Approved Risk; calling the gate's reject operation sets the lead Lost with reason 'Underwriter declined' and ends the case at Lead Lost - Underwriter Declined. [Done when: A run paused at this gate resumes only via its named resume or reject operation
Resume with Approve or Approve with loading continues to rating
Reject sets the lead Lost with reason 'Underwriter declined' and ends the case
Neither operation has a time limit]
5. Publish lifecycle events at each milestone — Publish one event when a lead's agent assignment is finalized (auto or manager-assigned), one when a lead becomes Lost (any of the five lost paths, carrying the reason), one when a quote is generated or re-rated, and one when a policy is issued and the lead becomes Converted. Payloads are not specified by the contract, so each event carries only the lead/run identifier so subscribers can look up the record from the domain service. [Done when: Each of the four events fires exactly once at its milestone node during a run
The event bus receives the publish call even when the business call that triggered the milestone had to be retried first]
6. Wire every backend domain call with retry, backoff and error handling — Wire the 18 consumed operations/events from the backend domain service (register lead, duplicate lookup, auto-assign, agent directory lookup, capture risk, screen appetite, record underwriter outcome, rate quote, latest-quote lookups, record contact activity, validate/bind, reassign, lead lookup for access control, risk lookup) behind a single HTTP client with bounded retry and exponential backoff on timeout/5xx; on exhausted retries the run stays paused at its current node and the error is surfaced rather than guessing the result. [Done when: Every one of the 18 consumed operations/events has a calls entry naming the retry/backoff/on-failure behavior
A simulated backend timeout leaves the run paused at the same node instead of advancing]
7. Add automated tests for graph branching, gates and failure handling — Cover duplicate refusal, assignment fallback to the manager gate, appetite decline/refer branching, underwriter approve/approve-with-loading/decline, the re-rate loop, client accept/decline/expiry, bind validation failures, and a simulated backend failure leaving the run paused. [Done when: DRY_RUN=true python3 -m pytest -q passes covering duplicate refusal, assignment fallback to the manager gate, appetite decline/refer branching, underwriter approve/approve-with-loading/decline, the re-rate loop, client accept/decline/expiry, bind validation failures, and a simulated backend failure leaving the run paused]

## Requirements you own — every one needs code, and you must prove it
- [REQ-003] (must) Automatically assign lead via round-robin among active agents serving the lead's city; if no active agent serves that city, the case waits (no SLA, no auto-escalation) for an agency manager, who checks their queue themselves and chooses one active agent as soon as available. The lead is never left unassigned, and it is never assigned to two agents. Agent records, their city coverage, and active/inactive status are maintained as agent records within the same application by the manager.
- [REQ-007] (must) Underwriter decides on referred risk (Approve, Approve with loading, or Decline), with no formal SLA to act and no auto-escalation; underwriter checks the referral queue within the application themselves.

These are assigned to THIS service; no other worker is implementing them. A requirement is satisfied by CODE THAT RUNS — not by a database column named after it and never read, and not by one of two required channels.
Before you finish, write `ATTESTATION.json` at your service root: a JSON object
`{"version": 1, "service_key": "...", "requirements": [...]}` with one entry per requirement above, shaped
`{"req_key", "status": "implemented"|"partial"|"not_implemented", "file", "line", "symbol", "test", "note"}`.
`file`/`symbol` must name code you actually wrote that ENFORCES the rule (a schema column or a config key is not evidence); `test` is the test that fails if the requirement is removed. Anything you could not implement is `not_implemented` with a `note` — and also a `GAPS.json` entry. Declaring a gap is a finding for a human to review; a false claim is a defect the platform will catch, since every field here is checked against your code.

## Process flow you own — from the APPROVED process model (this is the control flow, not background reading)
Steps:
- `start [start]` Lead Registration Request
- `register_lead [automated]` Register New Lead
    Registers lead with customer's name, mobile number, email, city, source, and product Private Car. Status becomes New.
- `check_duplicate [decision]` Open Lead With Same Mobile And Vehicle Reg Exists?
    Sequential check for an existing open lead with the same mobile number and vehicle registration number.
- `duplicate_declined [declined]` Registration Refused - Duplicate Lead
- `auto_assign_agent [automated]` Auto-Assign Agent By Round-Robin
    Automatically assigns lead via round-robin among active agents serving the lead's city.
- `check_agent_available [decision]` Active Agent Available In City?
- `manager_manual_assign [human_gate]` Manager Assigns Agent From Queue
    Manager checks their queue and chooses one active agent as soon as available when no active agent serves the lead's city.
- `manage_agent_records [automated]` Maintain Agent Records
    Manager maintains agent records, their city coverage, and active/inactive status within the application.
- `capture_risk_data [automated]` Capture Risk Data
    Status becomes Capture until every required risk fact is present. Case does not continue while a required fact is missing. Lead remains in Capture indefinitely until the agent completes it.
- `check_risk_complete [decision]` All Required Risk Facts Present?
- `auto_screen_appetite [automated]` Auto-Screen Appetite
    Automatically screens appetite with ordered decline/refer rules; first match wins; no added human review step.
- `check_screen_outcome_decline [decision]` Appetite Screen Result Is Decline?
- `lead_lost_decline_screen [declined]` Lead Lost - Declined By Screening
    Decline sets lead to Lost with that reason and the case ends. A lost lead is not a conversion.
- `check_screen_outcome_refer [decision]` Appetite Screen Result Is Refer?
- `underwriter_review_referral [human_gate]` Underwriter Decides On Referred Risk
    Underwriter checks referral queue themselves and decides Approve, Approve with loading, or Decline. No formal SLA, no auto-escalation.
- `check_underwriter_decision [decision]` Underwriter Declined Risk?
- `lead_lost_underwriter_decline [declined]` Lead Lost - Underwriter Declined
    Underwriter decline sets lead Lost with reason 'Underwriter declined' and the case ends.
- `record_underwriter_outcome [automated]` Record Underwriter Approval Outcome
    Records the underwriter's Approve or Approve with loading decision on the risk as the latest approved risk.
- `auto_rate_quote [automated]` Auto-Rate Latest Approved Risk
    Automatically rates the latest approved risk from the agency rate card and stores a new quote version with breakdown, time, and expiry at end of seventh day. Status becomes Quoted. Only this rate card is used. Fully automatic with no added review step.
- `record_contact_activity [automated]` Record Agent Contact Activity
    Records agent contact activities on the lead: date/time, agent, channel, outcome, note, optional next follow-up date. Activities are never edited or deleted.
- `agent_rerate_decision [decision]` Agent Changes Risk And Re-Rates Before Acceptance?
    Before acceptance, agent may change risk and rate again; each rate stores a new quote version. Only the latest version can be accepted; a declined, expired, or replaced version cannot be bound.
- `client_decision_wait [automated]` Wait For Client Accept, Decline, Or Expiry
    Waits for client to accept or decline the quote, or for the seventh day to end with no acceptance.
- `check_client_outcome_accept [decision]` Client Accepted Quote?
- `check_client_outcome_decline [decision]` Client Declined Quote?
- `lead_lost_client_decline [declined]` Lead Lost - Client Declined
    Client decline records a reason (price, bought elsewhere, or not interested) and sets lead Lost.
- `lead_lost_quote_expired [declined]` Lead Lost - Quote Expired
    The seventh day ends with no acceptance: the application automatically sets the lead to Lost with reason 'Quote expired'. Nobody has to choose this.
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
- `end_converted [end]` Lead Converted
- `end_reassign [end]` Reassignment Complete
- `end_access_counts [end]` Access And Reporting Available

Transitions:
- `start -> register_lead`
- `register_lead -> check_duplicate`
- `check_duplicate -> duplicate_declined`  [yes]
- `check_duplicate -> auto_assign_agent`  [no]
- `auto_assign_agent -> check_agent_available`
- `check_agent_available -> capture_risk_data`  [yes]
- `check_agent_available -> manager_manual_assign`  [no]
- `manager_manual_assign -> capture_risk_data`
- `capture_risk_data -> check_risk_complete`
- `check_risk_complete -> capture_risk_data`  [no]
- `check_risk_complete -> auto_screen_appetite`  [yes]
- `auto_screen_appetite -> check_screen_outcome_decline`
- `check_screen_outcome_decline -> lead_lost_decline_screen`  [yes]
- `check_screen_outcome_decline -> check_screen_outcome_refer`  [no]
- `check_screen_outcome_refer -> underwriter_review_referral`  [yes]
- `check_screen_outcome_refer -> auto_rate_quote`  [no]
- `underwriter_review_referral -> check_underwriter_decision`
- `check_underwriter_decision -> lead_lost_underwriter_decline`  [yes]
- `check_underwriter_decision -> record_underwriter_outcome`  [no]
- `record_underwriter_outcome -> auto_rate_quote`
- `auto_rate_quote -> record_contact_activity`
- `record_contact_activity -> agent_rerate_decision`
- `agent_rerate_decision -> capture_risk_data`  [yes]
- `agent_rerate_decision -> client_decision_wait`  [no]
- `client_decision_wait -> check_client_outcome_accept`
- `check_client_outcome_accept -> validate_bind_inputs`  [yes]
- `check_client_outcome_accept -> check_client_outcome_decline`  [no]
- `check_client_outcome_decline -> lead_lost_client_decline`  [yes]
- `check_client_outcome_decline -> lead_lost_quote_expired`  [no]
- `validate_bind_inputs -> bind_and_issue_policy`
- `bind_and_issue_policy -> end_converted`
- `start -> manage_agent_records`
- `manage_agent_records -> end_access_counts`
- `start -> manager_reassign_lead`
- `manager_reassign_lead -> end_reassign`
- `start -> role_based_access_control`
- `role_based_access_control -> compute_counts_conversion`
- `compute_counts_conversion -> end_access_counts`

Entry: `start`.  Terminal: `duplicate_declined`, `lead_lost_decline_screen`, `lead_lost_underwriter_decline`, `lead_lost_client_decline`, `lead_lost_quote_expired`, `end_converted`, `end_reassign`, `end_access_counts`.

Build EXACTLY this graph. Every step above is a node in your compiled runtime graph and every transition is an edge in it. A transition carrying a condition is a CONDITIONAL edge, and two conditions leaving one step MUST route to different targets — mapping both to the same next step deletes the business rule the branch came from. Writing a handler function for a step and not adding that step to the compiled graph does NOT implement it: the function is unreachable and the run flows past it. Before you finish, walk this list and confirm every step and every transition is present in the compiled graph.

## Human gates — execution MUST STOP here (2 in this flow)

### `manager_manual_assign` — Manager Assigns Agent From Queue
- The run PAUSES at this node and does not advance without a recorded human decision.

### `underwriter_review_referral` — Underwriter Decides On Referred Risk
- The run PAUSES at this node and does not advance without a recorded human decision.

A gate is implemented only when ALL of these hold: the gate node is IN the compiled graph; the run HALTS there with no human input; its decision's branches go to DIFFERENT targets; and the resume/reject operations move the run out of the halt. Gate handler functions plus approve/reject endpoints with no halt in the graph is precisely the failure this section exists to prevent — it looks complete, passes its unit tests, and auto-approves every single case.


## Tests you MUST write (the platform INSTALLS your deps and ACTUALLY RUNS these with pytest — a failing test blocks Gate 4, not just a collection error)
- Declare the test toolchain in your INSTALLED manifest (requirements.txt or a `test` extra) and set `[tool.pytest.ini_options] asyncio_mode = "auto"`: pytest, pytest-asyncio, pytest-mock, and whichever of respx/responses matches your HTTP client (respx only intercepts httpx; responses only intercepts requests).
- Put every test under `tests/`. Most tests run under `DRY_RUN=true` with NO real network / DB / secrets — fake those at the boundary. But DRY_RUN stubs ONE seam, not your business logic: at least one test per dependency client MUST run with `DRY_RUN=false` against the stubbed transport and assert the real request URL/method/body/auth header — a suite that is 100% DRY_RUN has verified nothing about your actual integration code. Never pin `DRY_RUN` at module scope or in an autouse fixture; set it per-test only.
- Settings must bind env via `Field(alias="DRY_RUN")` / `Field(alias="DATABASE_URL")` (and the same pattern for every other env key). Do not rely on a second lowercase `dry_run` env var — the harness emits `DRY_RUN` only.
- `.env.example` must not pin live infrastructure URLs. Leave `DATABASE_URL` blank or unset so the harness and local loops use in-memory storage/checkpointing.
- Never return empty `{}` from a LangGraph node that runs after a writer on a structural edge; re-emit the prior `result`/`error` (explicit passthrough) or return `None` only when no prior channel write must be preserved. An empty update after a writer raises `InvalidUpdateError` and aborts the request.
- Tests MUST import the same module tree the Dockerfile CMD runs; importing orphan root files (e.g. `from main import app` when CMD is `src.package.main:app`) is a gate failure.
- Do NOT create a second implementation at the clone root or a parallel package name — exactly ONE canonical tree under `./services/orchestrator/`.
- Use src-layout: application code under `src/<package>/`, never `main.py` or `graph.py` at the service root (the layout gate blocks flat root trees).
- An "imports cleanly" test (importing the app/graph must not raise) and, for HTTP services, a `/health` test.
- One test per endpoint in "Your API contract" above: call it and assert the status code plus the `response_example` shape.
- One contract test per dependency in the FROZEN block: feed its frozen `response_example` through your typed client with respx/monkeypatch — never call a live dependency.
- REQUIRED end-to-end test `tests/test_workflow_e2e.py`: construct the initial graph state, fake EVERY dependency client at the boundary (using the frozen `response_example`s), invoke the compiled graph to a terminal state, and assert the happy path plus at least one branch. This is the workflow test the platform runs end-to-end.
- REQUIRED gate test, one per entry in "Human gates" above: run the graph from the trigger with every dependency faked and assert the run HALTS at that gate — it has NOT reached the gate's downstream target and no write/commit side effect fired. Then resume via the declared approve operation and assert it proceeds; separately reject and assert it lands on the REJECT branch's target, not the happy path. A suite that never asserts a halt cannot tell your graph apart from one that auto-approves every case.
- Before you finish, verify against the TEXT of your graph module that every node function you defined is passed to `add_node`, every decision function is passed to `add_conditional_edges`, and no conditional mapping sends all of its outcomes to the same target. An unregistered node does NOT fail loudly — the graph compiles, imports and passes its tests, and the step simply never happens.

## Approved plan
## Lead-to-Policy Orchestrator — build plan

### What this service owns
This FastAPI + LangGraph service owns only the control-flow skeleton of the private-car lead lifecycle: the start node, every decision node, the two human gates, every "lead lost" terminal node, and the three end states (Lead Converted, Reassignment Complete, Access And Reporting Available). Every business read/write (register lead, auto-assign, capture risk, screen appetite, record underwriter outcome, rate the quote, record contact activity, validate and bind, reassign, access control, counts) is owned by the backend domain service and is reached only through calls. This service stores no entities of its own.

### Workflow & human gates
A run starts via the trigger operation (new lead intake, a reassignment request, or an access-and-reporting request). The main pipeline runs: duplicate check → round-robin auto-assignment → (if no active agent covers the city) pause at the Manager Assigns Agent From Queue gate, with no SLA and no auto-escalation, until the manager resumes it with a chosen active agent → risk capture loop until complete → automatic appetite screening (first-match decline/refer) → decline ends the case Lost; refer pauses at the Underwriter Decides On Referred Risk gate, with no SLA and no auto-escalation, until the underwriter resumes it (approve / approve with loading) or rejects it (decline, ending the case Lost with reason "Underwriter declined") → automatic rating stores a quote version → an activity is recorded → the agent may re-rate (loop back to capture) or proceed to the client decision wait → client accepts (go to bind validation), declines (Lost with reason), or the seventh day ends with no acceptance (Lost with reason "Quote expired", nobody chooses this) → bind validation checks the effective date and collected amount → policy issued, lead Converted.

Both gates have no timeout and no automatic escalation: the manual agent-assignment gate and the underwriter referral-decision gate both wait until the named resume/reject operation is called, with no formal time limit and no auto-escalation to anyone else.

### Tasks
1. Scaffold the FastAPI + LangGraph service and the health check.
2. Build the workflow graph (all owned nodes) and the trigger entry point.
3. Implement the Manager Assigns Agent From Queue human gate (resume only).
4. Implement the Underwriter Decides On Referred Risk human gate (resume and reject).
5. Publish the four lifecycle events (agent assigned, lead lost, quote issued, policy issued).
6. Wire all 18 consumed backend calls with bounded retry and exponential backoff; on exhausted retries the run stays at its current node rather than guessing an outcome.
7. Add automated tests for every branch, both gates, and a simulated backend failure.

### Failure policy
No frozen failure policy was given for the owned nodes. Both human gates wait indefinitely with no SLA and no auto-escalation. Calls to the backend domain service use bounded retry with exponential backoff; on exhausted retries the run is left paused at its current node and the error is surfaced, never guessed.

### Out of scope
No entity storage, no business validation logic, and no UI screens — all owned by other services.


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

Write code ONLY inside this workspace, only for `orchestrator`. Follow the approved plan —
do not expand scope. Prefer small, runnable files over large frameworks.

