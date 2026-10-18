from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from ...core.paths import image_path
from ..dependencies import get_resources

router = APIRouter(tags=["images"])


@router.get("/images/{filename:path}")
def serve_image(filename: str, resources=Depends(get_resources)):
    directory = resources.settings.images_dir
    target = image_path(directory, filename)
    if target is None:
        raise HTTPException(status_code=404, detail="Image not found")
    if not target.is_file():
        target = image_path(directory, "placeholder.jpg")
    if target is None or not target.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(target)
