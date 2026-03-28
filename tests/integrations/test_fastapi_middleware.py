"""Tests for FastAPI middleware."""

from __future__ import annotations

from unittest.mock import MagicMock

from aigov_shield.integrations.fastapi_middleware import GovernanceMiddleware
from aigov_shield.prevention import GuardAction, PIIGuard


def test_middleware_init():
    app = MagicMock()
    guard = PIIGuard(on_violation=GuardAction.BLOCK)
    middleware = GovernanceMiddleware(app=app, guards=[guard])
    assert len(middleware.guards) == 1


def test_excluded_paths():
    app = MagicMock()
    middleware = GovernanceMiddleware(
        app=app,
        excluded_paths=["/health", "/metrics"],
    )
    assert "/health" in middleware.excluded_paths
    assert "/metrics" in middleware.excluded_paths
