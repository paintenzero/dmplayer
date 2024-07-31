from enum import Enum
from pydantic import BaseModel, Field


class GlobalDirection(Enum):
    NORTH = 0
    WEST = 1
    SOUTH = 2
    EAST = 3


class MoveDirection(Enum):
    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"


class TurnDirection(Enum):
    LEFT = "left"
    RIGHT = "right"
    AROUND = "around"


class AiTool(BaseModel):
    name: str = Field(validation_alias="tool")
    arguments: dict = Field(validation_alias="tool_input")


class EAction(Enum):
    MOVE = 0
    TURN = 1


class Action:
    action: EAction
    args: any

    def __init__(self, action: EAction, args: any):
        self.action = action
        self.args = args
