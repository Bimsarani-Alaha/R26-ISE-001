import json
import httpx
import base64
import logging
from functools import cached_property
from pathlib import Path
from typing import Optional
from ..core.config import load_settings
from ..core.paths import image_path as resolve_image

logger = logging.getLogger(__name__)


class QwenService:
    def __init__(self, settings=None):
        self.settings = settings or load_settings()

    @cached_property
    def requirement_prompt(self):
        return self._load_prompt("requirement_prompt.txt")

    @cached_property
    def stylist_prompt(self):
        return self._load_prompt("stylist_prompt.txt")

    def _load_prompt(self, filename: str) -> str:
        path = self.settings.prompts_dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Prompt file not found: {path}")

    async def _call_ollama(self, prompt: str, images: list[str] = None, model: Optional[str] = None) -> str:
        model = model or self.settings.qwen_model
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        is_stylist = model == self.settings.qwen_stylist_model
        endpoint = "generate"
        answer_prefix = "{"
        if is_stylist:
            # This Qwen3-VL thinking variant ignores think=False on generate.
            # A nonempty assistant prefill makes its chat renderer close the
            # thinking block and its parser collect answer content directly.
            endpoint = "chat"
            payload.pop("prompt")
            payload["messages"] = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer_prefix},
            ]
            payload["think"] = False
            payload["options"] = {"num_predict": 768, "temperature": 0.2}
            # JSON grammar starts at a fresh object, so do not combine it with
            # a prefilled opening brace. The prompt specifies the JSON schema.
        else:
            payload["format"] = "json"
        if images:
            encoded_images = []
            for img_path in images:
                path = Path(img_path)
                if path.exists():
                    with open(path, "rb") as f:
                        encoded_images.append(base64.b64encode(f.read()).decode("utf-8"))
            if encoded_images:
                if is_stylist:
                    payload["messages"][0]["images"] = encoded_images
                else:
                    payload["images"] = encoded_images

        headers = {"ngrok-skip-browser-warning": "true"}
        # Image encoding and reasoning take longer than text extraction locally.
        timeout = self.settings.qwen_stylist_timeout if model == self.settings.qwen_stylist_model else 180.0
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Calling Ollama model {model} at {self.settings.ollama_base_url}/api/{endpoint} (timeout={timeout}s)")
                response = await client.post(f"{self.settings.ollama_base_url}/api/{endpoint}", json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                if is_stylist:
                    if result.get("done_reason") == "length":
                        return json.dumps({"error": "Styling generation reached its token limit before finishing. Please try again with a shorter request."})
                    content = result.get("message", {}).get("content", "")
                    if not content.strip():
                        return json.dumps({"error": "The styling model returned no answer. Check the Ollama model logs."})
                    # Ollama returns only the continuation, excluding the prefix.
                    return answer_prefix + content
                return result.get("response", "")
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:2000]
            try:
                body = e.response.json()
                if isinstance(body, dict) and body.get("error"):
                    detail = str(body["error"])[:2000]
            except ValueError:
                pass
            message = f"Model request failed (HTTP {e.response.status_code}): {detail}"
            logger.error("Ollama model %s: %s", model, message)
            return json.dumps({"error": message})
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

        # Resolve product image so the vision model scans image + metadata together.
        raw_image_ref = image_path or product_metadata.get("image_path")
        resolved = self._resolve_image(raw_image_ref) if raw_image_ref else None
        images = [resolved] if resolved else None
        if resolved:
            logger.info(f"Stylist vision: sending image {resolved} to {self.settings.qwen_stylist_model}")
        else:
            logger.info("Stylist vision: no product image found, using text-only advice")

        raw_response = await self._call_ollama(full_prompt, images=images, model=self.settings.qwen_stylist_model)
        return self._parse_json_response(raw_response)

    def _resolve_image(self, image_path: str) -> Optional[str]:
        if not image_path:
            return None
        path = resolve_image(self.settings.images_dir, image_path)
        return str(path) if path is not None and path.is_file() else None

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
                response = await client.get(f"{self.settings.ollama_base_url}/api/tags", headers=headers)
                if response.status_code != 200:
                    logger.warning(f"Ollama returned status {response.status_code}")
                    return False
                content_type = response.headers.get("content-type", "")
                if "application/json" not in content_type:
                    logger.warning(f"Ollama returned non-JSON response (Content-Type: {content_type})")
                    return False
                data = response.json()
                models = data.get("models", [])
                installed = {m.get("name") for m in models}
                return {self.settings.qwen_model, self.settings.qwen_stylist_model}.issubset(installed)
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            return False


