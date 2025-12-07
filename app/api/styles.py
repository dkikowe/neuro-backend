from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/styles", tags=["styles"])


class Style(BaseModel):
    id: str
    name: str
    description: str


@router.get("", response_model=List[Style])
def get_styles() -> List[Style]:
    """
    Get list of available image generation styles.
    
    No authentication required.
    """
    return [
        Style(
            id="anime",
            name="Anime",
            description="Transform image into anime style"
        ),
        Style(
            id="realistic",
            name="Realistic",
            description="Enhance image with realistic details"
        ),
        Style(
            id="cartoon",
            name="Cartoon",
            description="Convert image to cartoon style"
        ),
        Style(
            id="oil-painting",
            name="Oil Painting",
            description="Transform image into oil painting style"
        ),
        Style(
            id="watercolor",
            name="Watercolor",
            description="Convert image to watercolor painting style"
        ),
        Style(
            id="sketch",
            name="Sketch",
            description="Transform image into pencil sketch"
        ),
    ]

