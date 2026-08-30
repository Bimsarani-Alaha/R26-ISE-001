import os
import unittest
from unittest.mock import patch

import health_tips


class HealthTipsEnvTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_health_tips_uses_ollama_model_for_body_appearance_guide(self):
        previous_model = os.environ.get("OLLAMA_MODEL")
        previous_base_url = os.environ.get("OLLAMA_BASE_URL")
        os.environ["OLLAMA_MODEL"] = "qwen2.5:3b"
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

        try:
            with patch("health_tips._call_ollama", return_value="Your balanced silhouette suits structured tops and tailored fits."):
                guidance = await health_tips.generate_health_tips(
                    shoulder_width=42,
                    hip_size=40,
                    height=170,
                    gender="woman",
                    clothing_size="M",
                )

            self.assertIn("structured tops", guidance.lower())
            self.assertIn("balanced", guidance.lower())
        finally:
            if previous_model is None:
                os.environ.pop("OLLAMA_MODEL", None)
            else:
                os.environ["OLLAMA_MODEL"] = previous_model

            if previous_base_url is None:
                os.environ.pop("OLLAMA_BASE_URL", None)
            else:
                os.environ["OLLAMA_BASE_URL"] = previous_base_url


if __name__ == "__main__":
    unittest.main()
