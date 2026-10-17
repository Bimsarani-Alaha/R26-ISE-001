import os
import unittest
from unittest.mock import patch

import health_tips


class HealthTipsEnvTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_health_tips_includes_available_measurements_safely(self):
        previous_model = os.environ.get("OLLAMA_MODEL")
        previous_base_url = os.environ.get("OLLAMA_BASE_URL")
        os.environ["OLLAMA_MODEL"] = "qwen2.5:3b"
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

        try:
            with patch(
                "health_tips._call_ollama",
                return_value="Choose movement that feels comfortable and nourishing.",
            ) as call_ollama:
                guidance = await health_tips.generate_health_tips(
                    " M ",
                    height_cm=168,
                    shoulder_cm=39,
                    hip_cm=96,
                )

            self.assertIn("comfortable", guidance.lower())
            prompt = call_ollama.call_args.args[0]
            self.assertIn('predicted clothing size is "M"', prompt)
            self.assertIn('"height_cm": 168', prompt)
            self.assertIn('"shoulder_cm": 39', prompt)
            self.assertIn('"hip_cm": 96', prompt)
            self.assertIn("cannot determine health", prompt)
            self.assertIn("Do not recommend weight loss/gain", prompt)
            self.assertNotIn('"gender":', prompt.lower())
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
