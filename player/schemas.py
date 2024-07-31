def move_schema() -> str:
    return {
        "type": "function",
        "function": {
            "name": "move",
            "description": "Move a character in specified directions",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "Direction to move the character. Possible values are: forward, backward, right, left",
                    }
                },
                "required": ["directions"],
            },
        },
    }


def turn_schema() -> str:
    return {
        "type": "function",
        "function": {
            "name": "turn",
            "description": "Turn character in specified direction",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "Direction to turn the character. Possible values: right, left, around",
                    }
                },
                "required": ["direction"],
            },
        },
    }


def lookaround_schema() -> str:
    return {
        "type": "function",
        "function": {
            "name": "lookaround",
            "description": "Look around the character's current location and describe the surroundings.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }


def read_manual_schema() -> str:
    return {
        "type": "function",
        "function": {
            "name": "read_manual",
            "description": "Search manual for specific topic and get top-k results",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to search for in the manual.",
                    },
                    "topk": {
                        "type": "integer",
                        "description": "Number of results to return. Defaults to 3",
                    },
                },
                "required": ["topic"],
            },
        },
    }
