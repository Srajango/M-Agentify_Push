---

## Service: approval-ui

- kind: ui
- title: Approval UI
- origin: new
- tech_stack: language=typescript, frontend_framework=react
- plan_status: approved
- assigned stack skill(s): `stack.react` (`.opencode/skills/stack-react/SKILL.md`), `stack.ts-contracts` (`.opencode/skills/stack-ts-contracts/SKILL.md`) — open the path in brackets for the FULL body; the
  non-negotiable subset is inlined below so you cannot miss it

## Hard rules from your assigned skills — these are NOT optional reading

## Code Quality Standards (TypeScript - NON-NEGOTIABLE)

**Type Safety - No `any` Type:**
```typescript
// ❌ WRONG: using any
function processData(data: any): any {
  return data.result;
}

// ✅ RIGHT: explicit types
interface ProcessInput {
  id: number;
  data: Record<string, unknown>;
}

interface ProcessOutput {
  status: 'success' | 'error';
  result?: string;
}

function processData(input: ProcessInput): ProcessOutput {
  return { status: 'success', result: input.data.toString() };
}
```

**Request Validation - Zod or class-validator Required:**
```typescript
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
  age: z.number().positive().optional(),
});

type CreateUserRequest = z.infer<typeof CreateUserSchema>;

router.post('/users', async (req, res) => {
  const parsed = CreateUserSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: parsed.error });
  }
  // parsed.data is validated and typed
});
```

**Async/Await - Always Handle Promises:**
```typescript
// ❌ WRONG: missing await
async function getUser(id: number) {
  const user = userService.findById(id);  // Returns Promise, not User!
  return user.email;  // Crashes at runtime
}

// ✅ RIGHT: await async calls
async function getUser(id: number): Promise<User> {
  const user = await userService.findById(id);
  return user;
}

// ✅ RIGHT: use Promise.all for parallel
async function getUsers(ids: number[]): Promise<User[]> {
  return Promise.all(ids.map(id => userService.findById(id)));
}
```

**Error Handling - Custom Exception Classes:**
```typescript
class NotFoundError extends Error {
  constructor(resource: string, id: any) {
    super(`${resource} with id ${id} not found`);
  }
}

try {
  const user = await userService.getUser(id);
} catch (error) {
  if (error instanceof NotFoundError) {
    return res.status(404).json({ error: error.message });
  }
  throw error;
}
```

**Testing - Vitest + Supertest Required:**
```typescript
describe('POST /users', () => {
  it('should create user', async () => {
    const res = await request(app)
      .post('/users')
      .send({ email: 'test@example.com', name: 'Test' });
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('id');
  });

  it('should reject invalid email', async () => {
    const res = await request(app)
      .post('/users')
      .send({ email: 'not-an-email', name: 'Test' });
    expect(res.status).toBe(400);
  });
});
```

**Coverage Requirement - 85%+ enforced:**
- `npm test -- --coverage`
- Line + branch coverage >= 85%
- All async paths tested
- All error cases tested


### From `stack.react`
## Non-negotiable rules — the build harness checks each of these

1. **Ship `tsconfig.json` and a test runner.** The platform runs `npm install`, `tsc --noEmit`, then
   your `vitest`/`jest` suite in a container. No `tsconfig.json` is a `build_failure`; no runner in
   devDependencies is `missing_test`.
2. **`tsc --noEmit` must be clean.** Do not silence a type error with `any` or `@ts-ignore`.
3. **Call only the endpoints in your FROZEN dependency contracts.** A path that is not in a
   producer's `api_surface` is `contract_mismatch`, even if it looks obviously right.
4. **Test behaviour, not snapshots.** Render the component, drive it the way a user would, and
   assert what changed. Fake HTTP at the boundary; never call a live dependency.

### From `stack.ts-contracts`
## Non-negotiable rules — verify each one before you stop

1. **Every function you define is called, or deleted.** Dead code reads to a reviewer as a shipped
   capability.
2. **An assertion that cannot fail is not a test.** Never widen an assertion, `skip`, or delete a
   test to make a suite pass over a defect you already found — fix the code, or declare it in
   `GAPS.json` with `"severity": "blocking"` and leave the strict assertion failing.
3. **Mock the module the code RESOLVES**, not the specifier you happen to type.
4. **Never fabricate a value** to fill a gap — the platform's fabrication scanner treats it as a
   gating blocker.
5. **`tsc --noEmit` must pass, and your test suite must actually run** — the platform compiles and
   executes what you ship.

## Workspace Boundaries (CRITICAL)

All commands MUST respect workspace and service boundaries. This prevents permission escalation errors that block builds.

### Command Constraints

**DO use these patterns:**
- `find .` or `find ./` (search current directory)
- `grep -r . ` (search current workspace)
- `grep -r . services/approval-ui/` (search own service)
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
| Search service | `find services/approval-ui/` | `find / ...` |

### Reference

- Workspace root: `/work/` (mounted at `./`)
- Service directory: `/work/services/approval-ui/` (accessed as `./services/approval-ui/`)
- Read-only reference: `/repo/` (if applicable)
- Scratch space: `/tmp/` (temporary files only)

Never reference absolute paths like `/work`, `/repo`, or `/` in commands. Use relative paths (`.` or `./`) within your service directory.

## Identifiers this plan already verified against the repository
Already checked against the repo identifier index at Gate 3 — use these exact names, do not rename or re-derive them.
- `src/app/App.tsx` (module)
- `src/api/orchestratorClient.ts` (module)
- `src/features/managerAssign/ManagerAssignQueue.tsx` (module)
- `src/features/managerAssign/ManagerAssignDecision.tsx` (module)
- `src/features/underwriterReferral/ReferralQueue.tsx` (module)
- `src/features/underwriterReferral/ReferralDecision.tsx` (module)


## Reviewer change request (REWORK — modify the EXISTING code in `./services/approval-ui/`, do not rebuild from scratch)
### Reviewer note for `approval-ui`
The frozen contract has no queue-list operation and no method or path for the three human-gate calls. Keep the calls already in orchestratorClient.ts. In GAPS.json, set the two blocking entries (the queue-list gap and the human-gate method/path gap) to severity advisory so they stop holding Gate 4. Do not add a second set of paths. Do not edit the orchestrator or lead-domain-service.

## Contract slice (FROZEN v3, hash `sha256:7b8c861e0e8c69d28d234e872c03e7601f41dc6b2c12a6047cb9bdc067a3d460`)
This is the authoritative boundary of this service. Implement every operation in `service.provides` exactly (method, path, fields, errors, idempotency key); call every entry in `consumed` and read only the fields listed in `service.consumes[].fields_used`; honour `failure_policy` timeouts and retries on those calls.

```json
{
 "consumed": {
  "op_bc42e7eadaa65523": {
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
  "op_ce482f80d0fcea34": {
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
  "op_e24ddacd8a90f3a1": {
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
  }
 },
 "consumed_owner": {
  "op_bc42e7eadaa65523": "svc_8118635b113f4724ad87",
  "op_ce482f80d0fcea34": "svc_8118635b113f4724ad87",
  "op_e24ddacd8a90f3a1": "svc_8118635b113f4724ad87"
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
    "op_id": "op_ce482f80d0fcea34"
   },
   {
    "fields_used": [],
    "op_id": "op_e24ddacd8a90f3a1"
   },
   {
    "fields_used": [],
    "op_id": "op_bc42e7eadaa65523"
   }
  ],
  "key": "approval-ui",
  "kind": "ui",
  "origin": "new",
  "owns_entities": {},
  "owns_nodes": [],
  "owns_requirements": [],
  "provides": [],
  "publishes": [],
  "service_uid": "svc_992c5968aab6457e8c86"
 },
 "status_vocabularies": {}
}
```

## Calls you MUST make (declared in your approved plan)
- `? ?` on `orchestrator`
- `? ?` on `orchestrator`
- `? ?` on `orchestrator`
A `webhook` entry means the dependency calls YOU back — implement and publish the callback endpoint named above. Replacing it with a poll is a different system, not an implementation detail. A field listed under a call was VERIFIED to exist at Gate 3 — read it from the response; do not fabricate a substitute if it looks absent.

## Dependency contracts (FROZEN — build against these, never redesign them)
A path parameter may be written `{name}`, `<converter:name>`, or `:name`. Those are the same segment. Call it with your stack's own syntax.
### `orchestrator`
- Reference mock (Prism) may be available at http://mock-orchestrator:5097 for inspecting example responses — you are NOT required to call it; implement to the contract below.
- `GET /health` — health

## Ordered tasks
1. Scaffold the app shell and the orchestrator API client — Create the React + TypeScript project using only Material UI components, set up routing between a Manager area and an Underwriter area, and add the API client wrapper the decision screens will use to call the orchestrator. [Done when: Running the app shows a shell with navigation to a Manager area and an Underwriter area
The orchestratorClient module exposes a resume call for manager_manual_assign, a resume call for underwriter_review_referral, and a reject call for underwriter_review_referral, each with a request timeout and a typed retryable-error result]
2. Build the manager's assignment queue and decision screen — Build the waiting list and decision screen for the Manager Assigns Agent From Queue gate. The decision screen calls the orchestrator's resume action for this gate to resume the paused lead with the chosen active agent. [Done when: The Manager Assignment Queue screen lists every lead waiting for manual assignment, with loading, empty and error states
Selecting an active agent on the Assign Agent Decision screen and confirming calls the orchestrator's resume action for this gate and removes the lead from the queue on success
A failed resume call shows a retryable error and keeps the lead in the queue]
3. Build the underwriter's referral queue and decision screen — Build the waiting list and decision screen for the Underwriter Decides On Referred Risk gate. The decision screen calls the orchestrator's resume action for this gate for Approve or Approve with loading, and the orchestrator's reject action for this gate for Decline. [Done when: The Underwriter Referral Queue screen lists every risk waiting for a referral decision, with loading, empty and error states
Choosing Approve or Approve with loading on the Referral Decision screen and confirming calls the orchestrator's resume action for this gate and removes the risk from the queue on success
Choosing Decline on the Referral Decision screen and confirming calls the orchestrator's reject action for this gate and removes the risk from the queue on success
A failed resume or reject call shows a retryable error and keeps the risk in the queue]
4. Add tests for both gates' screens and verify the suite passes — Add unit and component tests for both gates' waiting lists and decision screens, including success and failure paths of every call to the orchestrator, and verify the full test suite passes. [Done when: Automated tests cover the loading, empty and error states of both waiting lists
Automated tests cover a successful and a failed call for each of the three orchestrator actions from their decision screens
DRY_RUN=true python3 -m pytest -q (or the project's equivalent test runner) completes with all tests passing]

## Human gates — execution MUST STOP here (2 in this flow)

### `manager_manual_assign` — 
- The run PAUSES at this node and does not advance without a recorded human decision.

### `underwriter_review_referral` — 
- The run PAUSES at this node and does not advance without a recorded human decision.

A gate is implemented only when ALL of these hold: the gate node is IN the compiled graph; the run HALTS there with no human input; its decision's branches go to DIFFERENT targets; and the resume/reject operations move the run out of the halt. Gate handler functions plus approve/reject endpoints with no halt in the graph is precisely the failure this section exists to prevent — it looks complete, passes its unit tests, and auto-approves every single case.


## Tests you MUST write (the platform runs `npm ci`, then `tsc --noEmit`, then your `test` script for real — a type error or a failing test blocks Gate 4)
- Declare the toolchain in `package.json` devDependencies and wire `"scripts": {"build": "tsc", "test": "jest --ci"}` (or `vitest run`). The platform runs `npm run test` — a package with no `test` script fails the gate as `missing_test`. Author the scripts only; NEVER run `npm install` or any script yourself.
- Use jest + ts-jest + supertest (or vitest + supertest). Emit machine-readable results: for vitest add `--reporter=junit --outputFile=.smoke-junit.xml`; jest's `--ci` output is parsed directly. Test files are `*.test.ts` under `tests/`, mirroring `src/`.
- Drive `supertest` against the app exported from `src/app.ts` — never start a real listener in a test, and never bind a port.
- `tsconfig.json` must have `"strict": true` and compile cleanly under `tsc --noEmit`. Do not silence a type error with `any`, `@ts-ignore`, or by excluding `tests/` from the program — the typecheck runs over everything you wrote.
- Most tests run under `DRY_RUN=true` with NO real network / DB / secrets — fake those at the boundary. But DRY_RUN stubs ONE seam, not your business logic: at least one test per dependency client MUST run with `DRY_RUN=false` against a stubbed transport (`nock`, `msw`, or an injected fetch double) and assert the real request URL/method/body/auth header. A suite that is 100% DRY_RUN has verified nothing about your integration code. Never set `DRY_RUN` in `jest.setup.ts`, a global setup file, or at module scope — set it per-test.
- Read env through one typed config module (`process.env.DRY_RUN`, `process.env.DATABASE_URL`) with a zod schema; the harness emits UPPERCASE keys only.
- `.env.example` must not pin live infrastructure URLs. Leave `DATABASE_URL` blank or unset so the harness and local loops use in-memory storage.
- Tests MUST import the same module tree the Dockerfile CMD runs. If CMD is `node dist/server.js`, tests import `src/app.ts` — not a duplicate app defined in the test file, and not an orphan file at the clone root.
- Do NOT create a second implementation at the clone root or a parallel package — exactly ONE canonical tree under `./services/approval-ui/`, with its own `package.json`.
- An "imports cleanly" test (importing the app must not throw) and, for HTTP services, a `GET /health` test.
- One contract test per dependency in the FROZEN block: feed its frozen `response_example` through your typed client with `nock`/`msw` or a stubbed fetch — never call a live dependency.
- Before you finish, verify every module and every function you created is imported and reachable from the entrypoint. A function nothing calls is dead code to delete, not a capability you shipped.

## Approved plan
## Approval UI

A React + TypeScript single-page app, built only with Material UI components, that owns no business data and no backend operations. It renders the human side of two human gates and sends the person's decision back to the orchestrator.

### Screens
**Manager Assigns Agent From Queue gate**
- *Manager Assignment Queue* — a list of leads waiting because no active agent covers their city. Loading, empty and error states.
- *Assign Agent Decision* — lets the manager pick a different active agent for one queued lead and confirm; on confirm it calls the orchestrator's resume action for this gate.

**Underwriter Decides On Referred Risk gate**
- *Underwriter Referral Queue* — a list of risks waiting for an underwriter decision. Loading, empty and error states.
- *Referral Decision* — lets the underwriter choose Approve, Approve with loading, or Decline for one queued risk and confirm; Approve and Approve with loading call the orchestrator's resume action for this gate, Decline calls the orchestrator's reject action for this gate.

### Tasks
1. Scaffold the app shell and the orchestrator API client.
2. Build the manager's assignment queue and decision screen.
3. Build the underwriter's referral queue and decision screen.
4. Add tests for both gates' screens and verify the suite passes.

### Out of scope
Business records (leads, risks, quotes, policies, activities), process sequencing, role-based access enforcement, and counts/conversion reporting all live in other services; this UI only displays what it is handed and forwards the decision.



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

Write code ONLY inside this workspace, only for `approval-ui`. Follow the approved plan —
do not expand scope. Prefer small, runnable files over large frameworks.

