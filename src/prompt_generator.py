# -*- coding: utf-8 -*-

"""
AI Simscape Model Generator - Generating MATLAB Simscape Models using Large Language Models.
Copyright (C) 2024  Patrick Hummel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

--------------------------------------------------------------------------------------------

Prompt Generator

Last modification: 04.04.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from datetime import datetime

import tiktoken

from config.gobal_constants import PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE, \
    PATH_DEFAULT_LAST_GENERATED_PROMPT_TXT_FILE, OPENAI_GPT35_TURBO_INPUT_TOKENS_COST_USD_PER_1K, \
    PATH_DEFAULT_RESPONSES_DIR

from src import prompt_request_factory

from src.abstract_model.abstract_components import AbstractComponent
from src.language_model_enum import LLModel
from src.model.response import ResponseData
from src.tools.custom_errors import AbstractComponentError, AbstractConnectionError

DEFAULT_ABSTRACT_MODEL_RESPONSE_PATH = PATH_DEFAULT_RESPONSES_DIR / "api_call_20240208_1858/response_20240208_1858.json"

# Static, predefined parts of the prompts
GENERAL_PROMPT_PREFACE = "You are an electrical engineer."

ABSTRACT_MODEL_GENERATION_INSTRUCTIONS = ()

JSON_RESPONSE_INSTRUCTIONS = ("Only respond with a single JSON object that contains the components and "
                              "connections of the electrical circuit. Each component has a unique ID, "
                              "for example 'Resistor_0'. Each component has two or more ports, each with "
                              "a unique ID. For example 'Resistor_0_R1' for the right and 'Resistor_0_L1' "
                              "for the left port of a resistor. The components are connected via these "
                              "ports. Each connection consists of the attributes 'from' and 'to' which "
                              "have port ID as values. Each port needs to be part of a connection. Response "
                              "must only in JSON, no additional text.")


class PromptGenerator:

    def __init__(self, offline_mode: bool = False, temperature: float = 1.0):

        self.offline_mode = offline_mode
        self._temperature = temperature
        self._latest_specification_summary = ""

        # Load the JSON schema & validation instructions (only for basic prompt)
        self.json_response_schema = "Use the following JSON schema to validate your JSON, but don't include it in the response: "

        if PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE.is_file():
            with open(PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE, 'r') as file:
                json_schema_str: str = file.read()
        else:
            print(f"The file {PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE} does not exist.")

        self.json_response_schema += json_schema_str

        self.system_modeling_instructions = ""
        self.create_system_modeling_instructions()

    @property
    def temperature(self) -> float:
        return self._temperature

    @temperature.setter
    def temperature(self, value: float):

        # Temperature must be between 0.0 and 2.0
        if float(value) < 0.0:
            self._temperature = 0.0
        elif float(value) > 2.0:
            self._temperature = 2.0
        else:
            self._temperature = float(value)

    def create_system_modeling_instructions(self, selected_abstract_component_types_dict: dict = None) -> None:

        # If no dictionary is provided, allow all implemented abstract component types
        if selected_abstract_component_types_dict is None:
            selected_abstract_component_types_dict = AbstractComponent.get_implemented_component_types_dict()

        instructions = "Only the following components may be used: "

        for component in selected_abstract_component_types_dict.keys():
            instructions += f"{component}, "

        self.system_modeling_instructions = instructions

    def _save_prompt_and_response_to_disk(self, prompt_str: str, response_str: str) -> None:

        # Save complete response (debugging)
        datetime_now = datetime.now()
        datetime_now_str = datetime_now.strftime("%Y%m%d_%H%M")

        path_output_dir = PATH_DEFAULT_RESPONSES_DIR / f"api_call_{datetime_now_str}"

        if not path_output_dir.is_dir():
            path_output_dir.mkdir(parents=True)

        response_file = path_output_dir / f"response_{datetime_now_str}.txt"

        with open(response_file, 'w') as file:
            file.write(response_str)

        with open(PATH_DEFAULT_LAST_GENERATED_PROMPT_TXT_FILE, 'w') as file:
            file.write(prompt_str)

        print("-> Prompt saved to file.")

    def _calculate_input_tokens(self, prompt_str: str):

        # encoding = tiktoken.get_encoding("cl100k_base")
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(prompt_str))
        input_token_price_usd = (num_tokens / 1000) * OPENAI_GPT35_TURBO_INPUT_TOKENS_COST_USD_PER_1K

        print(f"-> Token count of prompt: {num_tokens} (min. expected cost: $ {input_token_price_usd})")

    def generate_prompt_custom(self, text: str, llm_model: LLModel) -> (str, ResponseData):

        # Send generated prompt as request
        response_data = prompt_request_factory.request(text, llm_model, self._temperature)

        return text, response_data

    def generate_prompt_create_specification_summary(self, usr: str, llm_model: LLModel) -> (str, ResponseData):

        final_prompt = (f"{GENERAL_PROMPT_PREFACE} "
                        f"Keep your response as short as possible and text only. "
                        f"Summarize the information from the following system specification: {usr} "
                        f"First, identify and list every component of the described electrical circuit. "
                        f"Second, identify and list all the connections between these components that are necessary "
                        f"to make a functional circuit matching the specification. "
                        f"Third, provide step by step instructions on how to correctly connect the components.")

        if self.offline_mode:

            response_data = ResponseData(response_str="No summary - Offline mode active...",
                                         input_tokens=15, output_tokens=15, time_seconds=5.0)

        else:

            # Send generated prompt as request
            response_data = prompt_request_factory.request(final_prompt, llm_model, self._temperature)

        return final_prompt, response_data

    def generate_prompt_create_abstract_model(self, system_description: str, llm_model: LLModel,
                                              save_to_disk: bool = True, function_call_prompt: bool = False) -> (str, ResponseData):

        # Save for future correction prompts
        self._latest_specification_summary = system_description

        final_prompt = (f"{GENERAL_PROMPT_PREFACE} You design electrical circuits based on a provided specification. "
                        f"You will analyze and identify all the necessary components and the connections between them "
                        f"from the following specification: {system_description} "
                        f"Design this electrical system and verify that this model is functional. Improve the model "
                        f"until it matches the specification and there are no problems. Each electrical circuit requires "
                        f"one or more power sources. Make sure all components are connected to form a complete and "
                        f"uninterrupted electrical circuit with at least one power source in the path. Electricity must "
                        f"be able to flow along the connections from the power source across components and back to the "
                        f"power source. "
                        f"{self.system_modeling_instructions} "
                        f"{JSON_RESPONSE_INSTRUCTIONS}")

        if self.offline_mode:

            with open(DEFAULT_ABSTRACT_MODEL_RESPONSE_PATH, 'r') as file:
                response: str = file.read()

            response_data = ResponseData(response_str=response, input_tokens=15, output_tokens=15, time_seconds=5.0)

        else:

            # Send generated prompt as request (either as a basic completion prompt or function call prompt)
            if function_call_prompt:

                response_data = prompt_request_factory.request_as_function_call(final_prompt, llm_model, self._temperature)

            else:

                # Append the JSON schema and validation instructions if using a basic completion prompt
                final_prompt += f" {self.json_response_schema}"

                response_data = prompt_request_factory.request(final_prompt, llm_model, self._temperature)

            if save_to_disk:
                self._save_prompt_and_response_to_disk(final_prompt, response_data.response_str)

        return final_prompt, response_data

    def generate_prompt_improve_abstract_model_by_feedback(self, abstract_system_model_json: str, feedback: str,
                                                           llm_model: LLModel, function_call_prompt: bool = False) -> (str, ResponseData):

        final_prompt = (f"{GENERAL_PROMPT_PREFACE} You design electrical circuits. "
                        f"The following JSON contains a model of a system with its components and connections. "
                        f"{abstract_system_model_json} Improve this model and the json using the following instructions: "
                        f"{feedback} {JSON_RESPONSE_INSTRUCTIONS}")

        if self.offline_mode:

            with open(DEFAULT_ABSTRACT_MODEL_RESPONSE_PATH, 'r') as file:
                response: str = file.read()

            response_data = ResponseData(response_str=response, input_tokens=15, output_tokens=15, time_seconds=5.0)

        else:

            # Send generated prompt as request (either as a basic completion prompt or function call prompt)
            if function_call_prompt:

                response_data = prompt_request_factory.request_as_function_call(final_prompt, llm_model, self._temperature)

            else:

                # Append the JSON schema and validation instructions if using a basic completion prompt
                final_prompt += f" {self.json_response_schema}"

                response_data = prompt_request_factory.request(final_prompt, llm_model, self._temperature)

        return final_prompt, response_data

    def generate_prompt_autocorrect_abstract_model(self, abstract_system_model_json: str, error: Exception | None,
                                                   llm_model: LLModel, function_call_prompt: bool = False) -> (str, ResponseData):

        if isinstance(error, AbstractComponentError):
            auto_correct_instruction = (f"There is a problem with a component. "
                                        f"Correct the model based on this error message: {error.message} "
                                        f"Problem with the following components: {str(error.list_wrong_components)}. "
                                        f"{self.system_modeling_instructions} "
                                        f"Make sure that every component name excluding the '_' and number is in the "
                                        f"list of possible components, if not, find the closest one and replace it.")

        elif isinstance(error, AbstractConnectionError):
            auto_correct_instruction = (f"There is a problem with a connection. "
                                        f"Correct the model based on this error message: {error.message}. "
                                        f"Problem with the following connections: {str(error.list_wrong_connections)}")

        elif error is None:

            auto_correct_instruction = (f"Compare this model to these specifications: "
                                        f"{self._latest_specification_summary} "
                                        f"Identify any differences. Next, correct these differences until the model"
                                        f"matches these specifications. Add or remove components and connections if needed."
                                        f"Change connections if needed. Return the updated model. "
                                        f"{self.system_modeling_instructions}")

        else:
            return

        final_prompt = (f"{GENERAL_PROMPT_PREFACE} You design electrical circuits based on a provided specification. "
                        f"The following JSON contains a model of a system with its components and connections: "
                        f"{abstract_system_model_json} "
                        f"Improve this model and the JSON using the following instructions: "
                        f"{auto_correct_instruction} Only return a single JSON object, not other text.")

        if self.offline_mode:

            with open(DEFAULT_ABSTRACT_MODEL_RESPONSE_PATH, 'r') as file:
                response: str = file.read()

            response_data = ResponseData(response_str=response, input_tokens=15, output_tokens=15, time_seconds=5.0)

        else:

            # Send generated prompt as request (either as a basic completion prompt or function call prompt)
            if function_call_prompt:

                response_data = prompt_request_factory.request_as_function_call(final_prompt, llm_model, self._temperature)

            else:

                # Append the JSON schema and validation instructions if using a basic completion prompt
                final_prompt += f" {self.json_response_schema}"

                response_data = prompt_request_factory.request(final_prompt, llm_model, self._temperature)

        return final_prompt, response_data
