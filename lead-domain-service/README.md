# Lead & Policy Domain Service

Owns the Private Car motor-insurance lead lifecycle end to end: intake and
duplicate blocking, round-robin agent assignment, risk capture, appetite
screening, underwriting, rate-card quoting with re-rating, agent contact
activities, client accept/decline/expiry, bind validation and policy
issuance, role-scoped visibility, and agency reporting counts.

## What it does

- Registers a new Private Car lead and blocks a duplicate open lead by
  mobile number + vehicle registration number (sequential check).
- Assigns the lead to an active agent in its city by round-robin (or a
  manager's explicit pick), and lets a manager reassign an open lead.
- Captures risk data until every required fact is present, then runs
  ordered first-match-wins appetite screening (decline / refer / clear).
- Records the underwriter's approve / approve-with-loading / decline
  outcome on a referred risk; an approval automatically triggers rating.
- Rates the latest approved risk against the one agency rate card
  (Third Party / Comprehensive, no-claim bonus, loading, rounded to the
  nearest rupee), storing a new quote version each time and replacing the
  prior one.
- Logs append-only agent contact activities.
- Records the client's accept / decline, and automatically lapses a quote
  to Lost ("Quote expired") once its seventh day ends with no acceptance.
- Validates the bind inputs (effective date, collected amount) and issues
  a unique `PC-{year}-{6 digits}` policy, converting the lead.
- Serves role-scoped lead visibility (agent / underwriter / manager) and
  live agency/agent conversion counts.
- Publishes `lead-registered`, `lead-status-changed`, `quote-issued` and
  `policy-issued` domain events to the orchestrator event bus, and accepts
  the orchestrator's workflow events (manual assignment made, underwriter
  decision made, client accepted, client declined) for audit correlation.

## Environment variables

See `.env.example`. All are read once at startup into `lead_domain.config.Settings`:

| Variable | Purpose |
| --- | --- |
| `DRY_RUN` | `true` (default) logs outbound domain events instead of sending them; `false` POSTs them to `ORCHESTRATOR_EVENTS_URL`. |
| `DATABASE_URL` | PostgreSQL URL for production, using the psycopg3 dialect this service installs (`postgresql+psycopg://user:password@host:5432/dbname`). Leave blank/unset to use an in-process SQLite database (tests and local loops). |
| `ORCHESTRATOR_EVENTS_URL` | Where domain events are POSTed when `DRY_RUN=false`. |
| `RATE_CARD_THIRD_PARTY_BASE_PREMIUM` | The agency rate card's flat third-party premium for Private Car. |
| `RATE_CARD_OWN_DAMAGE_RATE` | The agency rate card's own-damage rate applied to IDV. |

## Running locally

```bash
pip install -r requirements.txt
uvicorn lead_domain.main:app --reload --app-dir src
```

## Schema migrations

Production schema changes are authored as Alembic migrations under
`migrations/versions/` (see `migrations/env.py`, `alembic.ini`). Apply them
against a real PostgreSQL instance with:

```bash
alembic upgrade head
```

The in-process SQLite fallback used by tests and local dev builds its
schema directly from `lead_domain.models` instead of running Alembic.

## Tests

```bash
DRY_RUN=true python3 -m pytest -q
```

Every endpoint in the API surface has a happy-path, a validation-failure
and a business-error test; the process graph's nodes and transitions are
asserted against the approved process model; and the event publisher has
one dedicated test per domain event plus a `DRY_RUN=false` test against a
stubbed transport (`respx`) that asserts the real request.
