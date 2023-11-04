from ..config import settings
from fastapi import APIRouter

conversionRouter = APIRouter(prefix="/conversion")


@conversionRouter.post("/convert_tiff_to_png", status_code=201)
def convert_tiff_to_png(base64_img: str):
    """
    Converts the input TIFF to PNG.
    This is used by the web interface for visualization purposes
    """
    return settings.converter.convert_tiff_to_png(base64_img)
