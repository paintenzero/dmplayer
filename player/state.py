from pydantic import BaseModel
from PIL import Image
from typing import List, Tuple
from player.vision import VisionRectangle
from player.types import GlobalDirection


class PlayerState(BaseModel):
    step: int = 0
    segments: List[VisionRectangle] = []  # segments (items) seen of the screen
    coordinates: Tuple[int, int] = (0, 0)
    direction: GlobalDirection = GlobalDirection.NORTH
