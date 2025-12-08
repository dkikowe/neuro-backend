from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from app.core.styles_catalog import get_public_styles

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
    return [Style(**style) for style in get_public_styles()]

