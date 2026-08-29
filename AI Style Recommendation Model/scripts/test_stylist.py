import asyncio
import httpx
import json

async def test():
    prompt = (
        'You are an AI fashion stylist. Analyze the product and provide styling tips. '
        'Return ONLY valid JSON with keys: summary, accessories, footwear, color_combinations, layering, occasion_tip, complementary_items. '
        'Product: Shirt, Blue, Party, Casual, Cotton, Solid, 1299. '
        'Customer needs: casual shirt for party. Occasion: Party'
    )
    payload = {"model": "qwen2.5:7b", "prompt": prompt, "stream": False}
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post("http://localhost:11434/api/generate", json=payload)
        resp.raise_for_status()
        result = resp.json()
        raw = result.get("response", "")
        
        # Parse like the app does
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.strip().startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            cleaned = "\n".join(json_lines)
        
        parsed = json.loads(cleaned)
        for key, val in parsed.items():
            print(f"  {key}: {type(val).__name__} = {repr(val)[:100]}")

asyncio.run(test())
