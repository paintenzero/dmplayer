import ollama
import player.schemas as schemas
import json
from player.types import AiTool
from llm_logger import LLMLogger


class SmartController:

    def __init__(self, video_game_name: str, model: str, logger: LLMLogger):
        self.model = model
        self.video_game_name = video_game_name
        self.logger = logger

    def parse_action_phrase(self, user_input: str):
        """Analyze action text and choose correct tool"""
        tools = [
            schemas.move_schema(),
            schemas.turn_schema(),
            schemas.lookaround_schema(),
            schemas.read_manual_schema(),
        ]
        system_message = f"""
You have access to the following functions:
{json.dumps(tools)}

You must follow these instructions:
Always select one or more of the above tools based on the user query
If a tool is found, you must respond in the JSON format matching the following schema:
{{
    "tools": [{{
        "tool": "<name of the selected tool>",
        "tool_input": <parameters for the selected tool, matching the tool's JSON schema
    }}]
}}
If there are multiple tools required, make sure a list of tools are returned in a JSON array.
If there is no tool that match the user request, you will respond with empty json.
Do not add any additional Notes or Explanations"""

        user_message = f"""You are controlling a classic RPG videogame called {self.video_game_name} from 90s.
Human writes you in plain text what to do next. You are deciding which combination of tools to use to perform the action.
User's input: {user_input}"""
        try:
            response_text = self.execute_prompt(system_message, user_message)
            tools_dict = json.loads(response_text)
            tools = []
            for t in tools_dict["tools"]:
                tool = AiTool.model_validate(t)
                tools.append(tool)
            return tools
        except Exception as e:
            print(f"Failed to parse tools: {e}")
            return []

    def execute_prompt(self, system_message: str, user_message: str) -> str:
        """Execute the prompt on ollama engine"""
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]
        response = ollama.chat(
            model=self.model,
            messages=messages,
        )
        self.logger.log_action_request(
            prompt=messages,
            response=response,
        )
        return response["message"]["content"]
