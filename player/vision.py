from PIL import Image
from pydantic import BaseModel
from typing import Tuple
import base64
import cv2
import numpy as np
from io import BytesIO
from openai import OpenAI
from llm_logger import LLMLogger


class VisionRectangle(BaseModel):
    x: int
    y: int
    width: int
    height: int
    color: Tuple[int, int, int]


class VisionModel:
    def __init__(self, video_game_name: str, logger: LLMLogger):
        self.video_game_name = video_game_name
        self.logger = logger

    def segment_gameview(self, image: Image) -> dict:
        # Convert the PIL image to a numpy array
        cv2_image = np.array(image)
        gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = np.ones((4, 4), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=3)
        sure_bg = cv2.dilate(opening, kernel, iterations=3)
        contours, hierarchy = cv2.findContours(
            sure_bg, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        rectangles = []
        for idx, c in enumerate(contours):
            if hierarchy[0][idx][3] != -1:
                continue
            boundRect = cv2.boundingRect(c)
            if boundRect[2] * boundRect[3] < 500:
                continue
            rect = VisionRectangle(
                x=boundRect[0],
                y=boundRect[1],
                width=boundRect[2],
                height=boundRect[3],
                color=(255, 0, 0),
            )
            rectangles.append(rect)
            cv2.rectangle(
                cv2_image,
                (rect.x, rect.y),
                (rect.x + rect.width, rect.y + rect.height),
                rect.color,
                2,
            )
        return (Image.fromarray(cv2_image), rectangles)

    # def analyze_gameview(
    #     screen: Image, openai: OpenAI, step: int, video_game_name: str
    # ) -> str:
    #     buffered = BytesIO()
    #     screen.save(buffered, format="PNG")
    #     base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    #     additional_info = ""

    #     prompt = f"""You are playing classic RPG videogame from 90s called {video_game_name}.
    #         {additional_info}
    #         Describe what you see on the screen. Be precise.
    #         Write in JSON format:
    #         {{
    #             "front": "what you see in front of the character.",
    #             "right": "what you see on right gameview.",
    #             "left": "What you see on the left in gameview.",
    #             "notes": "Any other notes to store for future references",
    #         }}

    #         Do not describe any UI elements like buttons."""

    #     response = openai.chat.completions.create(
    #         model="gpt-4o",
    #         temperature=0.0,
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": [
    #                     {
    #                         "type": "text",
    #                         "text": prompt,
    #                     },
    #                     {
    #                         "type": "image_url",
    #                         "image_url": {
    #                             "url": f"data:image/png;base64,{base64_image}"
    #                         },
    #                     },
    #                 ],
    #             }
    #         ],
    #     )
    #     response_text = response.choices[0].message.content
    #     log_vision_request(screen, prompt, response_text, step)
    #     return response_text
