import asyncio

import pytest


def payload(monkeypatch, fashionclip, cartographer, ollama=True):
    from app import main
    from app.services.fashionclip_service import fashionclip_service
    from app.services.cartographer_service import cartographer_service

    monkeypatch.setattr(fashionclip_service, "status", lambda: fashionclip)
    monkeypatch.setattr(cartographer_service, "status", lambda: cartographer)

    async def connected():
        return ollama

    monkeypatch.setattr(main.qwen_service, "check_connection", connected)
    monkeypatch.setattr(main.product_service, "_ensure_loaded", lambda: None)
    monkeypatch.setattr(main.product_service, "df", None)
    return asyncio.run(main._health_payload())


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
    from app.services.cartographer_service import CartographerService

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
    from app.services.fashionclip_service import FashionClipService

    service = FashionClipService(enabled=state != "disabled")
    if state == "loaded":
        service._worker = object()
    elif state == "unavailable":
        service._failed = True
    assert service.status() == expected