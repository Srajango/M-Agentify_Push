# Approval UI

A React + TypeScript single-page app, built only with Material UI components, that
renders the human side of two human gates in the loan/lead flow and sends the
person's decision back to the orchestrator:

- **Manager Assigns Agent From Queue** (`manager_manual_assign`) — a manager picks
  a different active agent for a lead and the app calls the orchestrator's resume
  action for that gate.
- **Underwriter Decides On Referred Risk** (`underwriter_review_referral`) — an
  underwriter approves (with or without loading) or declines a referred risk; the
  app calls the orchestrator's resume action for approve/approve-with-loading and
  its reject action for decline.

This service owns no business data of its own (`service.provides` is empty); it
only displays what the orchestrator hands it and forwards the person's decision.

## Environment variables

| Variable | When read | Purpose | Default |
|---|---|---|---|
| `VITE_ORCHESTRATOR_BASE_URL` | build time | Base URL the bundle calls for all orchestrator requests | `http://localhost:5096` |
| `VITE_ORCHESTRATOR_TIMEOUT_MS` | build time | Per-request timeout (ms) applied to every orchestrator call | `5000` |
| `DRY_RUN` | Node/test only, via `process.env` | When `true`, `src/api/orchestratorClient.ts` returns canned fixtures instead of calling the network. Has no `VITE_` prefix, so it is never baked into the browser bundle. | `false` |

Copy `.env.example` to `.env` and adjust `VITE_ORCHESTRATOR_BASE_URL` /
`VITE_ORCHESTRATOR_TIMEOUT_MS` for your environment before running `vite build`.

## Run / build / test

```bash
npm install        # installs the pinned dependency manifest (platform-run, not by this agent)
npm run dev         # local dev server (vite)
npm run build       # tsc --noEmit, then the production static build into dist/
npm test            # vitest run, with a JUnit report written to .smoke-junit.xml
npm run typecheck   # tsc --noEmit only
```

The `Dockerfile` builds the static bundle in a `node:20-alpine` stage and serves
`dist/` with `serve` on port `8080` in the runtime stage.

## Project layout

```
src/
  app/App.tsx                     # MUI app bar + tab navigation + routes
  api/config.ts                   # zod-validated env config (base URL, timeout, DRY_RUN)
  api/orchestratorClient.ts       # typed orchestrator client: health, queue reads, resume/reject
  components/QueueStates.tsx      # shared loading/error/empty presentational components
  features/managerAssign/         # manager queue + decision screen for manager_manual_assign
  features/underwriterReferral/   # underwriter queue + decision screen for underwriter_review_referral
tests/                            # vitest + @testing-library/react + msw, mirrors src/
```

## Gaps

See `GAPS.json` for the endpoints this service had to design without a frozen
shape (the frozen contract names the three orchestrator operations by `op_id`
only, with empty `request`/`response` schemas, and never names a queue-listing
endpoint at all).
