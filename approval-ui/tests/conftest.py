"""Pytest fixtures for approval-ui.

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
def mock_orchestrator():
    """Mock orchestrator service using FROZEN contract."""
    with respx.mock:
        respx.get('http://mock-orchestrator:5097/health').mock(
            return_value=Response(200, json={})
        )
        yield
