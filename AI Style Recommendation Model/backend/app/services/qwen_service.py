import json
import httpx
import base64
import logging
from pathlib import Path
from typing import Optional
from ..config import OLLAMA_BASE_URL, QWEN_MODEL, PROMPTS_DIR, IMAGES_DIR

logger = logging.getLogger(__name__)


class QwenService:
    def __init__(self):
        self.requirement_prompt = self._load_prompt("requirement_prompt.txt")
        self.stylist_prompt = self._load_prompt("stylist_prompt.txt")

    def _load_prompt(self, filename: str) -> str:
        path = PROMPTS_DIR / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Prompt file not found: {path}")

    async def _call_ollama(self, prompt: str, images: list[str] = None) -> str:
        payload = {
            "model": QWEN_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        if images:
            encoded_images = []
            for img_path in images:
                path = Path(img_path)
                if path.exists():
                    with open(path, "rb") as f:
                        encoded_images.append(base64.b64encode(f.read()).decode("utf-8"))
            if encoded_images:
                payload["images"] = encoded_images

        headers = {"ngrok-skip-browser-warning": "true"}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info(f"Calling Ollama at {OLLAMA_BASE_URL}/api/generate")
                response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            return json.dumps({"error": "Model request timed out. Please try again."})
        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama")
            return json.dumps({"error": "Cannot connect to the model. Please check if Ollama is running."})
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return json.dumps({"error": f"Model request failed: {str(e)}"})

    async def analyze_requirements(self, requirements_text: str) -> dict:
        full_prompt = f"{self.requirement_prompt}\n\nCustomer request:\n{requirements_text}"
        raw_response = await self._call_ollama(full_prompt)
        return self._parse_json_response(raw_response)

    async def generate_styling_tips(
        self,
        product_metadata: dict,
        customer_requirements: str,
        occasion: Optional[str] = None,
        image_path: Optional[str] = None,
    ) -> dict:
        key_fields = ["article_type", "base_colour", "occasion", "style", "material", "pattern", "price"]
        context_parts = []
        for key in key_fields:
            val = product_metadata.get(key)
            if val is not None:
                context_parts.append(f"{key}: {val}")

        context = ", ".join(context_parts)
        context += f". Customer needs: {customer_requirements}"
        if occasion:
            context += f". Occasion: {occasion}"

        full_prompt = f"{self.stylist_prompt}\n\n{context}"

        raw_response = await self._call_ollama(full_prompt)
        return self._parse_json_response(raw_response)

    def _resolve_image(self, image_path: str) -> Optional[str]:
        if not image_path:
            return None
        cleaned = str(image_path).replace("Images/", "").replace("images/", "")
        full_path = IMAGES_DIR / cleaned
        if full_path.exists():
            return str(full_path)
        return None

    def _parse_json_response(self, raw: str) -> dict:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
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
            raw = "\n".join(json_lines)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw": raw}

    async def check_connection(self) -> bool:
        try:
            headers = {"ngrok-skip-browser-warning": "true"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{OLLAMA_BASE_URL}/api/tags", headers=headers)
                if response.status_code != 200:
                    logger.warning(f"Ollama returned status {response.status_code}")
                    return False
                content_type = response.headers.get("content-type", "")
                if "application/json" not in content_type:
                    logger.warning(f"Ollama returned non-JSON response (Content-Type: {content_type})")
                    return False
                data = response.json()
                models = data.get("models", [])
                return any(m.get("name") == QWEN_MODEL for m in models)
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            return False


qwen_service = QwenService()
