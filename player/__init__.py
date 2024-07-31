import pyautogui
import os
from typing import Tuple
from player.types import MoveDirection, TurnDirection, GlobalDirection, Action, EAction
from player.smart_controller import SmartController
from player.vision import VisionModel
from player.state import PlayerState
from llm_logger import LLMLogger
from PIL import Image, ImageDraw, ImageFont
from time import sleep

VIEW_CHANGE_SLEEP = 0.3


class Player:
    """Class to represent an AI player for a game"""

    def __init__(self, game_controller_model: str):
        """Initialize the player."""
        self.video_game_name = "Dungeon Master"
        self.state = PlayerState()
        self.history = []
        self.logger = LLMLogger()
        self.smc = SmartController(
            video_game_name=self.video_game_name,
            model=game_controller_model,
            logger=self.logger,
        )
        dosbox = pyautogui.getWindowsWithTitle("DOSBox-X")
        if len(dosbox) < 1:
            raise Exception("Window with game not found!")
        self.dosbox_window = dosbox[0]
        self.ui_buttons_cache = {}
        self.screen = None
        self.segmentview = None
        self.vision = VisionModel(
            video_game_name=self.video_game_name,
            logger=self.logger,
        )
        self.next_step()

    def action_text(self, action: str):
        """Perform an action based on the given text."""
        tools = self.smc.parse_action_phrase(action)
        for tool in tools:
            self._execute_ai_tool(tool)
        return tools

    def new_game(self):
        """Start a new game."""
        x, y = self._get_ui_button_coordinates(Image.open("ui_elements/new_game.png"))
        if x > 0 or y > 0:
            self._mouse_click(x, y)

    def move(self, direction: MoveDirection):
        """Move the player in the given direction."""
        self.press_button(direction.value)
        if direction == MoveDirection.FORWARD:
            if self.state.direction == GlobalDirection.NORTH:
                self.change_coordinates((0, 1))
            elif self.state.direction == GlobalDirection.SOUTH:
                self.change_coordinates((0, -1))
            elif self.state.direction == GlobalDirection.EAST:
                self.change_coordinates((1, 0))
            elif self.state.direction == GlobalDirection.WEST:
                self.change_coordinates((-1, 0))
        elif direction == MoveDirection.BACKWARD:
            if self.state.direction == GlobalDirection.NORTH:
                self.change_coordinates((0, -1))
            elif self.state.direction == GlobalDirection.SOUTH:
                self.change_coordinates((0, 1))
            elif self.state.direction == GlobalDirection.EAST:
                self.change_coordinates((-1, 0))
            elif self.state.direction == GlobalDirection.WEST:
                self.change_coordinates((1, 0))
        if direction == MoveDirection.RIGHT:
            if self.state.direction == GlobalDirection.NORTH:
                self.change_coordinates((1, 0))
            elif self.state.direction == GlobalDirection.SOUTH:
                self.change_coordinates((-1, 0))
            elif self.state.direction == GlobalDirection.EAST:
                self.change_coordinates((0, -1))
            elif self.state.direction == GlobalDirection.WEST:
                self.change_coordinates((0, 1))
        elif direction == MoveDirection.LEFT:
            if self.state.direction == GlobalDirection.NORTH:
                self.change_coordinates((-1, 0))
            elif self.state.direction == GlobalDirection.SOUTH:
                self.change_coordinates((1, 0))
            elif self.state.direction == GlobalDirection.EAST:
                self.change_coordinates((0, 1))
            elif self.state.direction == GlobalDirection.WEST:
                self.change_coordinates((0, -1))
        self.history.append(Action(EAction.MOVE, direction))
        self.next_step()

    def change_coordinates(self, change: Tuple[int, int]):
        new_coordinates = (
            self.state.coordinates[0] + change[0],
            self.state.coordinates[1] + change[1],
        )
        self.state.coordinates = new_coordinates

    def turn(self, direction: TurnDirection):
        """Turn the player in the given direction."""
        direction_change = 0
        self.history.append(Action(EAction.TURN, direction))
        if direction == TurnDirection.AROUND:
            self.press_button(f"turnright")
            self.press_button(f"turnright")
            direction_change = 0
        else:
            self.press_button(f"turn{direction.value}")
            if direction == TurnDirection.LEFT:
                direction_change = 1
            else:
                direction_change = -1
        self.next_step(direction_change=direction_change)

    def lookaround(self):
        """Look in four directions and create a single image"""
        image_spacing = 5
        forward_image = self.get_gameview()
        self.turn(TurnDirection.RIGHT)
        sleep(VIEW_CHANGE_SLEEP)
        right_image = self.get_gameview()
        self.turn(TurnDirection.RIGHT)
        sleep(VIEW_CHANGE_SLEEP)
        back_image = self.get_gameview()
        self.turn(TurnDirection.RIGHT)
        sleep(VIEW_CHANGE_SLEEP)
        left_image = self.get_gameview()
        self.turn(TurnDirection.RIGHT)
        sleep(VIEW_CHANGE_SLEEP)
        aio_image = Image.new(
            "RGBA",
            (
                forward_image.width * 2 + image_spacing,
                forward_image.height * 2 + image_spacing,
            ),
        )
        aio_image.paste(forward_image, (0, 0))
        aio_image.paste(right_image, (forward_image.width + image_spacing, 0))
        aio_image.paste(left_image, (0, forward_image.height + image_spacing))
        aio_image.paste(
            back_image,
            (forward_image.width + image_spacing, forward_image.height + image_spacing),
        )
        draw = ImageDraw.Draw(aio_image)
        font = ImageFont.truetype("arialbd.ttf", 24)
        draw.text((10, 10), "Forward", fill="yellow", font=font)
        draw.text(
            (forward_image.width + image_spacing + 10, 10),
            "Right",
            fill="yellow",
            font=font,
        )
        draw.text(
            (10, forward_image.height + image_spacing + 10),
            "Left",
            fill="yellow",
            font=font,
        )
        draw.text(
            (
                forward_image.width + image_spacing + 10,
                forward_image.height + image_spacing + 10,
            ),
            "Back",
            fill="yellow",
            font=font,
        )
        return aio_image

    def press_button(self, button: str):
        """Find a button on screen and press it"""
        x, y = 0, 0
        if self.ui_buttons_cache.get(button) is None:
            filename = f"ui_elements/{button}.png"
            x, y = self._get_ui_button_coordinates(Image.open(filename))
            if x > 0 and y > 0:
                self.ui_buttons_cache[button] = (x, y)
        else:
            x, y = self.ui_buttons_cache.get(button)
        if x < 0 or y < 0:
            raise Exception(f"Could not find {button} button!")
        self._mouse_click(x, y)

    def _get_ui_button_coordinates(self, image: Image) -> tuple[int, int]:
        """Return center of the ui button passed as an image"""
        pyautogui.moveTo(self.dosbox_window.topleft.x, self.dosbox_window.topleft.y)
        game_image = self.make_screenshot()
        try:
            region = pyautogui.locate(
                needleImage=image, haystackImage=game_image, confidence=0.95
            )
            center = pyautogui.center(region)
            return center.x, center.y + 50
        except Exception as e:
            print(f"Could not find image on screen: {e}")
            return -1, -1

    def _mouse_click(self, x, y, left=True, absolute=False):
        """Click the mouse at the given coordinates."""
        _x = self.dosbox_window.topleft.x + x if not absolute else x
        _y = self.dosbox_window.topleft.y + y if not absolute else y
        pyautogui.click(_x, _y, button="left" if left else "right")

    def _execute_ai_tool(self, tool: dict):
        """Execute the given AI tool."""
        if tool.name == "move":
            self.move(MoveDirection(tool.arguments["direction"]))
        elif tool.name == "turn":
            self.turn(TurnDirection(tool.arguments["direction"]))

    def _activate_window(self):
        try:
            self.dosbox_window.activate()
        except:
            pass
        sleep(0.1)
        pyautogui.click(
            self.dosbox_window.topleft.x + 1, self.dosbox_window.topleft.y + 1
        )

    def next_step(self, direction_change: int = 0):
        self.state.step += 1
        self.state.direction = GlobalDirection(
            (self.state.direction.value + direction_change) % len(GlobalDirection)
        )
        sleep(VIEW_CHANGE_SLEEP)
        self.screen = self.make_screenshot()
        self.segmentview, self.state.segments = self.get_segmentview()

    def make_screenshot(self) -> Image:
        # if self.dosbox_window.isActive == False:
        # self._activate_window()
        aBox = (
            self.dosbox_window.topleft.x,
            self.dosbox_window.topleft.y + 50,
            self.dosbox_window.width,
            self.dosbox_window.height - 50,
        )
        return pyautogui.screenshot(region=aBox)

    def get_gameview(self) -> Image:
        return self.screen.crop((7, 67, 455, 338))

    def get_segmentview(self) -> Image:
        image = self.get_gameview()
        return self.vision.segment_gameview(image)


# def _start_new_game(self):
# self._mouse_click(505, 155)
# self.state.state = State.PLAYING


#     def _analyze_screen(self):
#         screen = self._get_screenshot()
#         response_text = analyze_gameview(
#             screen,
#             step=self.state.step,
#             openai=self.openai_client,
#             video_game_name=self.video_game_name,
#         )
#         self._analyze_screen_response(response_text)


#         self.openai_client = OpenAI(api_key=openai_key)
#         self.state = PlayerState()

#     def save_state(self) -> str:
#         with open(STATE_FILE, "w+") as file:
#             file.write(self.state.model_dump_json())

#     def load_state(self) -> bool:
#         if os.path.exists(STATE_FILE):
#             with open(STATE_FILE, "r") as file:
#                 self.state = PlayerState.model_validate_json(file.read())

#     def step(self):
#         if self.state.state == State.MENU:
#             self._start_new_game()
#         elif self.state.state == State.PLAYING:
#             # self._analyze_screen()
#             self.state.step += 1
