"""Shared fake-domain-client helpers for the e2e and human-gate tests.

Every dependency client method is faked at the boundary (monkeypatched on
the live ``DomainClient`` instance the runtime's graph closes over) using
values shaped like the frozen contract's (empty) response_example plus the
business fields this service's nodes read from them -- see GAPS.json for
which field names were assumed rather than verified.
"""

from __future__ import annotations

import datetime
from typing import Any
from unittest.mock import AsyncMock

TODAY = datetime.date.today().isoformat()

DEFAULT_RESPONSES: dict[str, Any] = {
    "register_lead": {"lead_id": "lead-123", "duplicate_found": False},
    "lookup_agent_directory": {"agents": [{"agent_id": "agent-1"}]},
    "auto_assign_agent": {"assigned": True, "agent_id": "agent-1"},
    "finalize_auto_assignment": {},
    "apply_manual_assignment": {},
    "notify_risk_incomplete": {},
    "lookup_risk": {"complete": True},
    "screen_appetite": {"outcome": "accept"},
    "rate_quote": {"quote_id": "quote-1", "total": 1200.0, "expiry": "2999-01-01"},
    "record_underwriter_outcome": {},
    "flag_rerate": {},
    "fetch_latest_quote_for_wait": {},
    "fetch_client_decision": {"client_outcome": "accept"},
    "fetch_quote_for_bind": {"total": 1200.0, "expiry": "2999-01-01"},
    "upsert_agent_record": {"stored": True},
    "reassign_lead": {},
    "lookup_lead": {"lead_id": "lead-123"},
    "publish_counts": {},
}


def install_fakes(client: Any, overrides: dict[str, Any] | None = None) -> Any:
    """Monkeypatch every DomainClient method the graph calls, in place."""

    overrides = overrides or {}
    for name, default in DEFAULT_RESPONSES.items():
        value = overrides.get(name, default)
        mock = AsyncMock(side_effect=value) if isinstance(value, list) else AsyncMock(return_value=value)
        setattr(client, name, mock)
    return client


def happy_path_trigger_payload() -> dict[str, Any]:
    return {
        "run_type": "lead",
        "lead": {
            "customer_name": "Asha Rao",
            "mobile_number": "9000000001",
            "email": "asha.rao@example.com",
            "city": "Pune",
            "source": "web",
            "vehicle_reg": "MH12AB1234",
        },
        "risk_data": {"make": "Toyota", "model": "Innova", "year": 2020},
        "bind_inputs": {"effective_date": TODAY, "amount_collected": 1200.0},
    }
