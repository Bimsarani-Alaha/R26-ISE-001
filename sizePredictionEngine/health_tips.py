import os
import logging
from pathlib import Path

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


async def generate_health_tips(
    shoulder_width: float,
    hip_size: float,
    height: float,
    gender: str,
    clothing_size: str = "unspecified",
) -> str:
    from google import genai

    proportion = shoulder_width / hip_size
    body_proportion = (
        "upper-body dominant"
        if proportion > 1.1
        else "lower-body dominant"
        if proportion < 0.9
        else "balanced"
    )
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        logger.error("GEMINI_API_KEY is not configured.")
        raise HealthTipsConfigurationError("GEMINI_API_KEY is not configured.")

    prompt = f"""Create a short personalized Body Appearance & Wellness Guide for this person. Make it different and specific to their gender, clothing size, body proportion, and measurements. Treat the clothing size as an indicator of estimated body frame, not health.

Give practical guidance covering fitness, simple meal planning, daily movement, mobility/posture, hydration, and sleep. For XS/S, focus on maintaining adequate nutrition, strength, energy, and fitness. For M, focus on maintaining balanced fitness and healthy routines. For L/XL, focus on regular cardio, strength, mobility, balanced meals, and sustainable activity. For 2XL/3XL/4XL, focus on low-impact and comfortable exercises, gradual activity progression, mobility, cardiovascular wellbeing, balanced portion-conscious meals, hydration, and sustainable daily routines. Adapt the advice further according to whether the person is upper-body dominant, lower-body dominant, or balanced.

Make the guide feel like a simple personal fitness and wellness plan rather than generic health advice. Do not recommend clothing, diagnose medical conditions, judge body size, or tell the person to lose or gain weight. Keep it positive, practical, concise, and easy to follow. Mention that measurements are estimates and not a medical assessment.

User data: gender {gender}; height {height:.1f} cm; shoulder width {shoulder_width:.1f} cm; hip width {hip_size:.1f} cm; body proportion {body_proportion}; clothing size {clothing_size}."""
    async with genai.Client(api_key=api_key).aio as client:
        interaction = await client.interactions.create(
            model=os.getenv("GEMINI_MODEL", "gemini-3.7-flash"),
            input=prompt,
        )
        guidance = getattr(interaction, "output_text", "")
        if not guidance:
            raise RuntimeError("Gemini returned no output text.")
        return guidance.strip()