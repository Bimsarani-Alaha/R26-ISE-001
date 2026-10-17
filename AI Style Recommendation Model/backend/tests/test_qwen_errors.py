import asyncio
import importlib
import json

import httpx
import pytest


@pytest.mark.parametrize("json_body", [True, False])
def test_ollama_http_error_preserves_server_reason(monkeypatch, caplog, json_body):
    service = importlib.import_module("app.services.qwen_service")
    reason = "Multimodal data provided, but model does not support multimodal requests."

    def respond(request):
        if json_body:
            return httpx.Response(400, json={"error": reason})
        return httpx.Response(400, text=reason)

    client_class = httpx.AsyncClient
    monkeypatch.setattr(
        service.httpx, "AsyncClient",
        lambda **kwargs: client_class(transport=httpx.MockTransport(respond), **kwargs),
    )
    result = json.loads(asyncio.run(service.QwenService()._call_ollama("Styling advice")))
    assert reason in result["error"]
    assert "400" in result["error"]
    assert reason in caplog.text


def test_generation_requests_json_output(monkeypatch):
    service = importlib.import_module("app.services.qwen_service")

    def respond(request):
        payload = json.loads(request.content)
        assert payload.get("format") == "json"
        return httpx.Response(200, json={"response": '{"occasion": ["Wedding"]}'})

    client_class = httpx.AsyncClient
    monkeypatch.setattr(
        service.httpx, "AsyncClient",
        lambda **kwargs: client_class(transport=httpx.MockTransport(respond), **kwargs),
    )
    result = asyncio.run(service.QwenService().analyze_requirements("Wedding lehenga"))
    assert result == {"occasion": ["Wedding"]}


@pytest.mark.parametrize("with_image", [True, False])
def test_requirements_and_styling_use_separate_models(monkeypatch, tmp_path, with_image):
    service = importlib.import_module("app.services.qwen_service")
    monkeypatch.setattr(service, "IMAGES_DIR", tmp_path)
    (tmp_path / "product.jpg").write_bytes(b"product image bytes")
    calls = []

    def respond(request):
        data = json.loads(request.content)
        calls.append(data)
        if request.url.path == "/api/chat":
            return httpx.Response(200, json={"message": {"content": '"summary":"Wedding outfit"}'}, "done_reason": "stop"})
        return httpx.Response(200, json={"response": '{"summary":"Wedding outfit"}'})

    client_class = httpx.AsyncClient
    monkeypatch.setattr(service.httpx, "AsyncClient", lambda **kwargs: client_class(
        transport=httpx.MockTransport(respond), **kwargs))
    svc = service.QwenService()
    asyncio.run(svc.analyze_requirements("Yellow lehenga for wedding"))
    result = asyncio.run(svc.generate_styling_tips(
        {"base_colour": "Yellow", "image_path": "product.jpg" if with_image else "missing.jpg"},
        "Yellow lehenga for wedding"))
    assert calls[0]["model"] == "qwen2.5:7b"
    assert "images" not in calls[0]
    assert calls[1]["model"] == "qwen3-vl:8b"
    assert "format" not in calls[1]
    assert calls[1]["messages"][-1] == {"role": "assistant", "content": "{"}
    assert 0 < calls[1]["options"]["num_predict"] <= 1024
    assert bool(calls[1]["messages"][0].get("images")) is with_image
    assert "Yellow" in calls[1]["messages"][0]["content"]
    assert result["summary"] == "Wedding outfit"


@pytest.mark.parametrize("installed,expected", [
    (["qwen2.5:7b"], False),
    (["qwen3-vl:8b"], False),
    (["qwen2.5:7b", "qwen3-vl:8b"], True),
])
def test_connection_requires_both_models(monkeypatch, installed, expected):
    service = importlib.import_module("app.services.qwen_service")
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, json={"models": [{"name": name} for name in installed]}))
    client_class = httpx.AsyncClient
    monkeypatch.setattr(service.httpx, "AsyncClient", lambda **kwargs: client_class(
        transport=transport, **kwargs))
    assert asyncio.run(service.QwenService().check_connection()) is expected


@pytest.mark.parametrize("body,expected", [
    ({"message": {"content": '"summary":'}, "done_reason": "length"}, "token limit"),
    ({"message": {"content": "", "thinking": "Still reasoning"}, "done_reason": "stop"}, "no answer"),
])
def test_stylist_reports_incomplete_generation(monkeypatch, body, expected):
    service = importlib.import_module("app.services.qwen_service")
    client_class = httpx.AsyncClient
    monkeypatch.setattr(service.httpx, "AsyncClient", lambda **kwargs: client_class(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body)), **kwargs))
    result = asyncio.run(service.QwenService().generate_styling_tips(
        {"article_type": "Dress", "base_colour": "White"}, "White dress for a party"))
    assert expected in result["error"].lower()
    assert "raw" not in result
