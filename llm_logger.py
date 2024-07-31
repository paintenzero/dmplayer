from PIL import Image
import os
from typing import Tuple, List


class LLMLogger:
    """Class for logging AI models requests and responses"""

    def __init__(self, log_dir: str = "./log"):
        self.log_dir = log_dir
        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir)

    def log_vision_request(self, image: Image, prompt: str, response: str, step: int):
        """Log a request-response to vision model"""
        image.save(f"{self.log_dir}/step{step}.png")
        with open(f"{self.log_dir}/prompt{step}.txt", "w+") as file:
            file.write(f"Prompt: {prompt}\n-----------\nResponse: {response}")

    def log_action_request(self, prompt: List[dict], response: object):
        """Log a request-response to vision model"""
        with open(f"{self.log_dir}/actions.txt", "a") as file:
            file.write(f"Prompt: {prompt}\n-----------\nResponse: {response}")
