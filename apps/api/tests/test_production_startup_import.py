import importlib


def test_production_application_entrypoint_imports_without_health_collision():
    main = importlib.import_module("app.main")
    health = importlib.import_module("app.health.checks")

    assert main.app is not None
    assert callable(health.run_health_checks)
    assert any(route.path == "/health" for route in main.app.routes)
