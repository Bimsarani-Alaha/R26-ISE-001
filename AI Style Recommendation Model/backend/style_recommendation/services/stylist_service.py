"""Styling workflow independent of HTTP request handling."""
from starlette.concurrency import run_in_threadpool
from ..core.errors import InferenceError, ProductNotFoundError
from ..schemas.models import StylistResponse
from .terminal_progress import PipelineProgress, new_request_id


def format_item(value):
    if not isinstance(value, dict):
        return str(value).strip()
    item = str(value.get("item", "")).strip()
    color = str(value.get("color", "")).strip()
    reason = str(value.get("reason", "")).strip()
    if color:
        item = f"{item} ({color})"
    return " — ".join(part for part in (item, reason) if part)


def to_str_list(value):
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, list):
        return [item for item in map(format_item, value) if item]
    return [value.strip()] if isinstance(value, str) and value.strip() else []


class StylistService:
    def __init__(self, requirements, catalog, qwen):
        self.requirements = requirements
        self.catalog = catalog
        self.qwen = qwen

    async def generate(self, request):
        product = await run_in_threadpool(self.catalog.get_product_by_id, request.product_id)
        if product is None:
            raise ProductNotFoundError("Product not found")
        progress = PipelineProgress(f"Stylist {new_request_id()}", total_stages=2)
        try:
            with progress.stage("Analyzing requirements"):
                preferences = await self.requirements.analyze(request.requirements)
            with progress.stage("Generating styling tips"):
                result = await self.qwen.generate_styling_tips(
                    product_metadata=product, customer_requirements=request.requirements,
                    occasion=", ".join(preferences.occasion) if preferences.occasion else None)
            if not isinstance(result, dict):
                raise InferenceError("The model returned invalid styling advice")
            if "error" in result:
                raise InferenceError(str(result["error"]))
            response = StylistResponse(
                summary=str(result.get("summary", "")).strip(),
                occasion_tip=str(result.get("occasion_tip", "")).strip(),
                **{key: to_str_list(result.get(key, [])) for key in (
                    "accessories", "footwear", "color_combinations", "layering", "complementary_items")})
            progress.finish()
            return response
        except Exception as error:
            progress.fail()
            if isinstance(error, InferenceError):
                raise
            raise InferenceError(str(error)) from error
        except BaseException:
            progress.fail()
            raise
        finally:
            progress.close()
