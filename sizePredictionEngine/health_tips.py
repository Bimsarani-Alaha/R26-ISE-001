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


async def generate_health_tips(
    shoulder_width: float,
    hip_size: float,
    height: float,
    gender: str,
    clothing_size: str = "unspecified",
) -> str:
    proportion = shoulder_width / hip_size if hip_size else 1.0
    body_proportion = (
        "upper-body dominant"
        if proportion > 1.1
        else "lower-body dominant"
        if proportion < 0.9
        else "balanced"
    )

    model = (os.getenv("OLLAMA_MODEL") or "qwen2.5:3b").strip()
    base_url = (os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").strip()

    if not model:
        raise HealthTipsConfigurationError("OLLAMA_MODEL is not configured.")
    if not base_url:
        raise HealthTipsConfigurationError("OLLAMA_BASE_URL is not configured.")

    logger.info("Using local Ollama model %s at %s", model, base_url)

    prompt = f"""You are a body appearance and wellness coach. Provide a warm, supportive, body-positive, and concise body appearance guide based on the following estimated measurements:
- Gender: {gender}
- Shoulder width: {shoulder_width} cm
- Hip width: {hip_size} cm
- Height: {height} cm
- Clothing size: {clothing_size}
- Body proportion: {body_proportion}

Focus on the person's overall body proportions, silhouette, posture, physical activity, mobility, hydration, balanced nutrition, and healthy daily habits. Explain the estimated body frame or proportion in a respectful and neutral way. Provide practical guidance that supports confidence, good posture, regular movement, and general wellbeing. Do not recommend clothing styles, necklines, waist emphasis, outfits, or fashion choices. Do not judge, rank, or label the body as attractive/unattractive, ideal/non-ideal, healthy/unhealthy, or use negative body-shaming language. Do not make medical claims, diagnose conditions, or suggest weight-loss or weight-gain targets. Make it clear that the measurements are estimates for general guidance and are not a medical assessment. Limit the response to 6-8 clear sentences."""

    return await asyncio.to_thread(_call_ollama, prompt, model, base_url)