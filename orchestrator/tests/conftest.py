"""Pytest fixtures for orchestrator.

Pre-built fixtures for mocking dependency services using their FROZEN contracts.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
import pytest
import respx
from httpx import Response
import json

# Add src/ to Python path for imports (handle src/ layout)
src_path = Path(__file__).parent.parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

@pytest.fixture(scope='function')
def enable_dry_run():
    """Enable DRY_RUN mode for tests that request it (opt-in, not forced).
    
    Fixture scope is 'function' for per-test isolation.
    NOT autouse — tests must explicitly request this fixture if they want DRY_RUN.
    This allows at least one test per client to run with DRY_RUN=false
    to verify the real HTTP/auth path executes (not stubbed).
    """
    old_dry_run = os.environ.get('DRY_RUN')
    os.environ['DRY_RUN'] = 'true'
    yield
    # Restore original state after each test
    if old_dry_run is not None:
        os.environ['DRY_RUN'] = old_dry_run
    else:
        os.environ.pop('DRY_RUN', None)

# Dependency mocking fixtures


@pytest.fixture
def mock_lead_domain_service():
    """Mock lead-domain-service service using FROZEN contract."""
    with respx.mock:
        respx.get('http://mock-lead-domain-service:5097/health').mock(
            return_value=Response(200, json={})
        )
        respx.post('http://mock-lead-domain-service:5097/agents').mock(
            return_value=Response(200, json={})
        )
        yield


@pytest.fixture
def client():
    """FastAPI TestClient for the orchestrator's own HTTP surface.

    Forces DRY_RUN=true for the duration of the test (opt-in via this
    fixture, not module-scoped or autouse) so the compiled graph's own
    control flow runs for real against a fresh ``OrchestratorRuntime``
    (built by the app's lifespan on TestClient startup) with no live
    lead-domain-service, DB, or secrets.
    """

    from fastapi.testclient import TestClient

    from orchestrator_app.config import get_settings
    from orchestrator_app.main import app

    old_dry_run = os.environ.get('DRY_RUN')
    os.environ['DRY_RUN'] = 'true'
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    if old_dry_run is not None:
        os.environ['DRY_RUN'] = old_dry_run
    else:
        os.environ.pop('DRY_RUN', None)
