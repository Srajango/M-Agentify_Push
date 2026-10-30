"""The app and the compiled process graph must import cleanly from the same
module tree the Dockerfile CMD boots (lead_domain.main:app)."""

from __future__ import annotations


def test_main_module_imports_cleanly() -> None:
    from lead_domain.main import app

    assert app.title == "Lead & Policy Domain Service"


def test_all_service_modules_import_and_register_handlers() -> None:
    from lead_domain import services  # noqa: F401
    from lead_domain.process_graph import NODES, registered_nodes

    assert registered_nodes() == set(NODES)
