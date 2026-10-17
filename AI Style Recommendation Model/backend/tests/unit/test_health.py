import asyncio

import pytest


def payload(monkeypatch, fashionclip, cartographer, ollama=True):
    import pandas as pd
    from style_recommendation.api.routes.health import health_payload
    from style_recommendation.core.resources import Resources
    resources = Resources()
    monkeypatch.setattr(resources.fashionclip, "status", lambda: fashionclip)
    monkeypatch.setattr(resources.cartographer, "status", lambda: cartographer)
    async def connected():
        return ollama
    monkeypatch.setattr(resources.qwen, "check_connection", connected)
    resources.catalog.df = pd.DataFrame()
    return asyncio.run(health_payload(resources))



def test_pending_rankers_are_healthy(monkeypatch):
    health = payload(monkeypatch, "pending", "pending")
    assert health["status"] == "healthy"
    assert health["rankers"] == {"fashionclip": "pending", "cartographer": "pending"}


def test_unavailable_ranker_reports_degraded(monkeypatch):
    # A latched-off ranker silently degrades ranking without failing requests.
    health = payload(monkeypatch, "unavailable", "loaded")
    assert health["status"] == "degraded"
    assert health["rankers"]["fashionclip"] == "unavailable"


def test_disabled_ranker_is_not_degraded(monkeypatch):
    health = payload(monkeypatch, "disabled", "disabled")
    assert health["status"] == "healthy"


@pytest.mark.parametrize("state,expected", [
    ("loaded", "loaded"),
    ("pending", "pending"),
    ("unavailable", "unavailable"),
    ("disabled", "disabled"),
])
def test_cartographer_status_reports_state(state, expected):
    from style_recommendation.inference.cartographer_service import CartographerService

    service = CartographerService(enabled=state != "disabled")
    if state == "loaded":
        service._model = object()
    elif state == "unavailable":
        service._failed = True
    assert service.status() == expected


@pytest.mark.parametrize("state,expected", [
    ("loaded", "loaded"),
    ("pending", "pending"),
    ("unavailable", "unavailable"),
    ("disabled", "disabled"),
])
def test_fashionclip_status_reports_state(state, expected):
    from style_recommendation.inference.fashionclip_service import FashionClipService

    service = FashionClipService(enabled=state != "disabled")
    if state == "loaded":
        service._worker = object()
    elif state == "unavailable":
        service._failed = True
    assert service.status() == expected