"""Import smoke test and the frozen GET /health endpoint test."""

from __future__ import annotations


def test_imports_cleanly() -> None:
    from orchestrator_app import graph, main, nodes, runtime  # noqa: F401

    assert hasattr(main, "app")


def test_health_returns_ok(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
