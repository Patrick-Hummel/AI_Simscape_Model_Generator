# -*- coding: utf-8 -*-

"""
Main module of the AI Simscape Model Generator.

Last modification: 28.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from pathlib import Path
from dotenv import load_dotenv

from config.gobal_constants import PATH_DEFAULT_RESPONSES_DIR
from src.language_model_enum import LLModel

# Load api-key as environment variable
load_dotenv(Path(".env"))

from src import prompt_request_factory
from src.prompt_generator import PromptGenerator
from src.response_interpreter import ResponseInterpreter
from src.simscape.interface import Implementer, SystemSimulinkAdapter
from src.system_builder import SystemBuilder

# Temporary to reuse old responses
SEND_NEW_REQUEST = False


def main():

    # 1) Generate prompt
    prompt_generator = PromptGenerator()
    prompt = prompt_generator.generate_prompt("Create a circuit with a battery, two lamps and two switches. "
                                              "Each lamp may be controlled by one switch.")

    # 2) Send prompt to LLM and await response
    if SEND_NEW_REQUEST:

        print("Sending new request...")
        response = prompt_request_factory.request(prompt, LLModel.OPENAI_GPT35_Turbo)

    else:

        print("Using a previous response...")
        previous_response = PATH_DEFAULT_RESPONSES_DIR / "api_call_20231128_1523/response_20231128_1523.txt"

        with open(previous_response, 'r') as file:
            response: str = file.read()

    # 3) Interpret response
    response_interpreter = ResponseInterpreter()
    abstract_system = response_interpreter.interpret_response(response)

    # 4) Build detailed system
    builder = SystemBuilder(abstract_system)
    system = builder.build("Example")
    # system.load_from_json_data()
    system.save_as_json()

    # 5) Create simulink model and save result to disk
    simulink_implementer = Implementer(SystemSimulinkAdapter)
    simulink_implementer.input_to_simulink(system, system.name)
    simulink_implementer.save_to_disk(system.name)


if __name__ == '__main__':
    main()
