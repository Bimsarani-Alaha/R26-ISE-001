import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / "server" / ".env")


class HealthTipsConfigurationError(RuntimeError):
    pass


async def generate_health_tips(
    shoulder_width: float,
    hip_size: float,
    height: float,
    gender: str,
) -> str:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HealthTipsConfigurationError("GEMINI_API_KEY is not configured.")

    prompt = f"""Provide concise, supportive body appearance guidance and general wellness tips for a clothing app user.
Use these measured values: shoulder width {shoulder_width:.1f} cm, hip size {hip_size:.1f} cm, height {height:.1f} cm, gender context {gender}.
Discuss proportion-aware styling, comfortable fit, posture or movement, and sustainable wellbeing habits. Do not diagnose conditions, estimate health risk, prescribe diet or exercise, or make claims about what a body should look like. Avoid judgmental language. Use a short heading and 4-6 practical bullet points in plain text."""

    async with genai.Client(api_key=api_key).aio as client:
        interaction = await client.interactions.create(
            model=os.getenv("GEMINI_MODEL", "gemini-3.7-flash"),
            input=prompt,
        )
        return interaction.output_text.strip()