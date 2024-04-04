# -*- coding: utf-8 -*-

"""
Main module of the AI Simscape Model Generator.

Last modification: 04.04.2024
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


def main():

    system_description = "Create a circuit with a battery, two lamps and two switches. Each lamp may be controlled by one switch."

    # 1) Generate prompt & send via request factory
    prompt_generator = PromptGenerator()
    prompt, response = prompt_generator.generate_prompt_create_abstract_model(system_description=system_description,
                                                                              llm_model=LLModel.OPENAI_GPT35_Turbo,
                                                                              save_to_disk=True,
                                                                              function_call_prompt=True)

    # 3) Interpret response
    response_interpreter = ResponseInterpreter()
    abstract_system = response_interpreter.interpret_abstract_model_json_response(response.response_str)

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
