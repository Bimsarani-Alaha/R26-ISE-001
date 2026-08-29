from fastapi import APIRouter, HTTPException
from ..schemas.models import StylistRequest, StylistResponse
from ..services.qwen_service import qwen_service
from ..services.product_service import product_service
from ..services.terminal_progress import PipelineProgress, new_request_id

router = APIRouter(prefix="/api/stylist", tags=["stylist"])


@router.post("", response_model=StylistResponse)
async def generate_stylist_tips(request: StylistRequest):
    if not request.product_id.strip():
        raise HTTPException(status_code=400, detail="Product ID is required")

    product = product_service.get_product_by_id(request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    req_id = new_request_id()
    progress = PipelineProgress(f"Stylist {req_id}", total_stages=2)

    try:
        with progress.stage("Analyzing requirements"):
            requirements = await qwen_service.analyze_requirements(request.requirements)
        print(f"[stylist] requirements parsed: {requirements}")

        if "error" in requirements:
            raise HTTPException(status_code=500, detail=requirements["error"])

        occasion = None
        if requirements.get("occasion"):
            occ = requirements["occasion"]
            if isinstance(occ, list):
                occasion = ", ".join(occ)
            else:
                occasion = str(occ)

        with progress.stage("Generating styling tips"):
            result = await qwen_service.generate_styling_tips(
                product_metadata=product,
                customer_requirements=request.requirements,
                occasion=occasion,
            )
        print(f"[stylist] styling tips parsed: {result}")

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        def format_item(v):
            if isinstance(v, dict):
                item = v.get("item", "")
                color = v.get("color", "")
                reason = v.get("reason", "")
                parts = [item]
                if color:
                    parts[0] = f"{item} ({color})"
                if reason:
                    parts.append(reason)
                return " — ".join(parts) if len(parts) > 1 else parts[0]
            return str(v)

        def to_str_list(val):
            if isinstance(val, list):
                return [format_item(v) for v in val]
            if isinstance(val, dict):
                return [format_item(v) for v in val.values()]
            if isinstance(val, str) and val:
                return [val]
            return []

        progress.finish()
        return StylistResponse(
            summary=result.get("summary", ""),
            accessories=to_str_list(result.get("accessories", [])),
            footwear=to_str_list(result.get("footwear", [])),
            color_combinations=to_str_list(result.get("color_combinations", [])),
            occasion_tip=result.get("occasion_tip", ""),
  
        )
    except HTTPException:
        progress.fail()
        raise
    except Exception as e:
        progress.fail()
        print(f"[stylist] ERROR: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
