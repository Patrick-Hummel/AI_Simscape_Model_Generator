# -*- coding: utf-8 -*-

"""
Main module of the AI Simscape Model Generator.

Last modification: 23.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import json
from pathlib import Path
from dotenv import load_dotenv

from config.gobal_constants import PATH_DEFAULT_DATA_JSON
from src.response_interpreter import ResponseInterpreter

# Load api-key as environment variable
load_dotenv(Path(".env"))


def main():

    # PromptRequestFactory.request("Hello World! (1)", LLM_MODEL_OPENAI_GPT)
    # PromptRequestFactory.request("Hello World! (2)", LLM_MODEL_OPENAI_GPT)
    # PromptRequestFactory.request("Hello World! (3)", LLM_MODEL_OPENAI_GPT)

    example_json_path = PATH_DEFAULT_DATA_JSON / "system_simple_motor_example.json"

    response_interpreter = ResponseInterpreter()

    try:

        # Convert Path to string before using json.loads
        with open(str(example_json_path), 'r') as file:
            json_data = json.load(file)

            # Interpret as if it were part of a LLM response
            response_interpreter.interpret_json(json_data)

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        exit(1)


if __name__ == '__main__':
    main()
