import asyncio
import json
import logging
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


logger = logging.getLogger(__name__)


def load_health_tips_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        logger.warning("Health tips .env file not found at %s", env_path)
        return

    load_dotenv(env_path, override=True)


load_health_tips_env()


class HealthTipsConfigurationError(RuntimeError):
    pass


def _call_ollama(prompt: str, model: str, base_url: str, retries: int = 3) -> str:
    """Call Ollama API with retry logic and improved error handling."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 300},
    }
    endpoint = f"{base_url.rstrip('/')}/api/generate"
    
    last_error = None
    for attempt in range(retries):
        try:
            logger.info(
                "Ollama request attempt %d/%d to %s with model %s",
                attempt + 1,
                retries,
                endpoint,
                model,
            )
            request = Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urlopen(request, timeout=120) as response:
                raw_body = response.read().decode("utf-8")
                
            response_json = json.loads(raw_body)
            guidance = str(response_json.get("response", "")).strip()
            
            if not guidance:
                error_msg = "Ollama returned no output text."
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            logger.info("Ollama request succeeded on attempt %d", attempt + 1)
            return guidance
            
        except json.JSONDecodeError as error:
            last_error = error
            logger.error("Ollama returned invalid JSON: %s", raw_body[:200])
            if attempt < retries - 1:
                wait_time = 2 ** attempt
                logger.info("Retrying in %d seconds...", wait_time)
                time.sleep(wait_time)
        except HTTPError as error:
            last_error = error
            logger.error(
                "HTTP Error %s: %s (attempt %d/%d)",
                error.code,
                error.reason,
                attempt + 1,
                retries,
            )
            if error.code == 503:
                logger.warning("Ollama service unavailable; model may be loading or service is overloaded")
            elif error.code == 500:
                logger.warning("Ollama internal error; check model and service logs")
            if attempt < retries - 1:
                wait_time = 2 ** attempt
                logger.info("Retrying in %d seconds...", wait_time)
                time.sleep(wait_time)
        except (URLError, TimeoutError) as error:
            last_error = error
            logger.error(
                "Connection error for Ollama at %s (attempt %d/%d): %s",
                base_url,
                attempt + 1,
                retries,
                error,
            )
            if attempt < retries - 1:
                wait_time = 2 ** attempt
                logger.info("Retrying in %d seconds...", wait_time)
                time.sleep(wait_time)
    
    # All retries exhausted
    raise RuntimeError(
        f"Ollama request failed after {retries} attempts for model {model}: {last_error}. "
        f"Please ensure: 1) Ollama is running at {base_url}, 2) Model '{model}' is pulled, "
        f"3) System has sufficient memory/resources."
    ) from last_error


async def generate_health_tips(clothing_size: str) -> str:
    normalized_size = clothing_size.strip()
    if not normalized_size:
        raise ValueError("A predicted clothing size is required for guidance.")

    model = (os.getenv("OLLAMA_MODEL") or "qwen2.5:3b").strip()
    base_url = (os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").strip()

    if not model:
        raise HealthTipsConfigurationError("OLLAMA_MODEL is not configured.")
    if not base_url:
        raise HealthTipsConfigurationError("OLLAMA_BASE_URL is not configured.")

    logger.info("Using local Ollama model %s at %s", model, base_url)

    prompt = f"""You are a supportive general-wellness guide. The only user information available is their predicted clothing size: {normalized_size}.

Give a warm, body-positive set of practical everyday wellness tips, such as comfortable movement, rest, hydration, balanced meals, and self-confidence. Do not infer body shape, proportions, fitness, health, gender, age, or lifestyle from clothing size. Explain briefly that clothing size is only an approximate fit label and is not a measure of health. Do not recommend weight loss or gain, diagnose conditions, make medical claims, judge bodies, or recommend outfits or fashion. Keep the advice general, respectful, and concise in 5-6 clear sentences."""

    return await asyncio.to_thread(_call_ollama, prompt, model, base_url)