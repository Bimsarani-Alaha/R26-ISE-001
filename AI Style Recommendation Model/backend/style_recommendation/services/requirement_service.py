"""Shared preference extraction and validation."""
from pydantic import ValidationError
from ..core.errors import InferenceError
from ..schemas.models import RequirementResponse


class RequirementService:
    def __init__(self, qwen):
        self.qwen = qwen

    async def analyze(self, text: str) -> RequirementResponse:
        result = await self.qwen.analyze_requirements(text)
        if not isinstance(result, dict):
            raise InferenceError("The model returned invalid requirements")
        if "error" in result:
            raise InferenceError(str(result["error"]))
        data = dict(result)
        occasion = data.get("occasion")
        if isinstance(occasion, str):
            occasion = [occasion]
        if isinstance(occasion, list) and all(isinstance(value, str) for value in occasion):
            occasion = [value.strip() for value in occasion if value.strip()] or None
        data["occasion"] = occasion
        try:
            return RequirementResponse.model_validate(data)
        except ValidationError as error:
            raise InferenceError("The model returned invalid requirements") from error
