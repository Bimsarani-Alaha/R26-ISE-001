"""Exercise the actual gateway interpreter when its local venv is available."""
from pathlib import Path
import subprocess

import pytest


def test_gateway_python_supports_style_contracts():
    root = next(parent for parent in Path(__file__).resolve().parents
                if (parent / "server/server.py").is_file())
    interpreter = root / "server/venv/Scripts/python.exe"
    if not interpreter.is_file():
        pytest.skip("Local gateway virtual environment is unavailable")
    script = Path(__file__).parents[1] / "serving_smoke.py"
    result = subprocess.run([str(interpreter), str(script)],
                            cwd=root / "AI Style Recommendation Model/backend",
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
