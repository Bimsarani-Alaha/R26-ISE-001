import os
import unittest

import health_tips


class HealthTipsEnvTests(unittest.TestCase):
    def test_load_health_tips_env_prefers_size_prediction_dotenv(self):
        previous_value = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = ""

        try:
            health_tips.load_health_tips_env()
            self.assertTrue(
                os.environ.get("GEMINI_API_KEY", "").startswith("AQ."),
                "The sizePredictionEngine .env should supply the Gemini key.",
            )
        finally:
            if previous_value is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = previous_value


if __name__ == "__main__":
    unittest.main()
