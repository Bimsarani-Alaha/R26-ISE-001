"""RED test: generate_styling_tips must scan product image + metadata via qwen3-vl."""
import asyncio
import json


def test_stylist_sends_image_to_qwen(tmp_path, monkeypatch):
    from app.services.qwen_service import QwenService

    # Create a fake image file so _resolve_image can find it
    from app import config
    img_name = "test_stylist_vision.jpg"
    img_file = config.IMAGES_DIR / img_name
    created = False
    try:
        if not img_file.exists():
            config.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            # minimal JPEG header bytes - only existence + readable bytes matter for base64 path
            img_file.write_bytes(bytes.fromhex("ffd8ffe000104a46494600010101006000600000ffd9"))
            created = True

        svc = QwenService.__new__(QwenService)
        # bypass prompt loading
        svc.requirement_prompt = "req"
        svc.stylist_prompt = "You are stylist. Return JSON."

        captured = {}

        async def fake_call(prompt: str, images=None):
            captured["prompt"] = prompt
            captured["images"] = images
            return json.dumps({
                "summary": "overview text",
                "accessories": ["watch"],
                "footwear": ["shoes"],
                "color_combinations": ["Black + White"],
                "layering": [],
                "occasion_tip": "tip",
                "complementary_items": ["bag"],
            })

        monkeypatch.setattr(svc, "_call_ollama", fake_call)

        product_metadata = {
            "product_id": "PTEST",
            "article_type": "Dress",
            "base_colour": "Black",
            "occasion": "Party",
            "style": "Elegant",
            "material": "Cotton",
            "pattern": "Solid",
            "price": 4500,
            "image_path": f"Images/{img_name}",
            "description": "Black elegant party dress",
        }

        result = asyncio.run(svc.generate_styling_tips(
            product_metadata=product_metadata,
            customer_requirements="I need a black elegant dress for a birthday party.",
            occasion="Birthday Party",
        ))

        # Must include overview/summary from model
        assert result.get("summary") == "overview text"
        # CRITICAL: image must be forwarded to qwen3-vl for vision scan
        assert captured.get("images"), "generate_styling_tips did not forward product image to qwen3-vl"
        assert len(captured["images"]) >= 1
        # Prompt must contain metadata + requirements + occasion
        prompt = captured.get("prompt", "")
        assert "Black" in prompt
        assert "birthday" in prompt.lower() or "Birthday Party" in prompt
    finally:
        if created and img_file.exists():
            img_file.unlink()


def test_stylist_missing_image_still_returns_text_advice(monkeypatch):
    """When image file is missing, stylist must still return text-based advice (no crash)."""
    from app.services.qwen_service import QwenService

    svc = QwenService.__new__(QwenService)
    svc.requirement_prompt = "req"
    svc.stylist_prompt = "You are stylist."

    async def fake_call(prompt: str, images=None):
        # Missing image -> images should be None/empty, but prompt must still work
        assert not images, "should not send images when file is missing"
        return json.dumps({
            "summary": "versatile styling overview",
            "accessories": ["scarf"],
            "footwear": ["flats"],
            "color_combinations": ["Blue + White"],
            "layering": [],
            "occasion_tip": "versatile tip",
            "complementary_items": [],
        })

    monkeypatch.setattr(svc, "_call_ollama", fake_call)

    result = asyncio.run(svc.generate_styling_tips(
        product_metadata={
            "article_type": "Shirt",
            "base_colour": "Blue",
            "image_path": "Images/DOES_NOT_EXIST_XYZ.jpg",
        },
        customer_requirements="I need a blue shirt.",
        occasion=None,
    ))
    assert result["summary"] == "versatile styling overview"
