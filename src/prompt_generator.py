# -*- coding: utf-8 -*-

"""
Prompt Generator

Last modification: 25.02.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from datetime import datetime

import tiktoken

from config.gobal_constants import PATH_DEFAULT_JSON_SCHEMA_FILE, PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE, \
    PATH_DEFAULT_LAST_GENERATED_PROMPT_TXT_FILE, PATH_DEFAULT_PROMPT_INSTRUCTIONS_JSON_RESPONSE, \
    PATH_DEFAULT_PROMPT_INSTRUCTIONS_PREFACE, OPENAI_GPT35_TURBO_INPUT_TOKENS_COST_USD_PER_1K, \
    PATH_DEFAULT_RESPONSES_DIR

from src import prompt_request_factory

from src.abstract_model.abstract_components import AbstractComponent
from src.language_model_enum import LLModel
from src.model.response import ResponseData
from src.tools.custom_errors import AbstractComponentError, AbstractConnectionError

DEFAULT_ABSTRACT_MODEL_RESPONSE_PATH = PATH_DEFAULT_RESPONSES_DIR / "api_call_20240208_1858/response_20240208_1858.json"


class PromptGenerator:

    def __init__(self, offline_mode: bool = False):

        self.offline_mode = offline_mode

        self.system_modeling_instructions = ""
        self.json_response_instructions = ""

        self._latest_specification_summary = ""

        self._create_system_modeling_instructions()
        self._create_json_response_instructions()

    def _create_system_modeling_instructions(self):

        implemented_abstract_component_types_dict = AbstractComponent.get_implemented_component_types_dict()

        instructions = "Only the following components may be used: "

        for component in implemented_abstract_component_types_dict.keys():
            instructions += f"{component}, "

        self.system_modeling_instructions += instructions

    def _create_json_response_instructions(self):

        instructions_file_path = PATH_DEFAULT_PROMPT_INSTRUCTIONS_JSON_RESPONSE

        if instructions_file_path.is_file():
            with open(instructions_file_path, 'r') as file:
                instructions_json_response: str = file.read()
        else:
            print(f"The file {instructions_file_path} does not exist.")

        # instructions_json_response += " Use the following JSON schema to validate your JSON, but don't include it in the response: "
        #
        # schema_file_path = PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE
        #
        # if schema_file_path.is_file():
        #     with open(schema_file_path, 'r') as file:
        #         json_schema_str: str = file.read()
        # else:
        #     print(f"The file {schema_file_path} does not exist.")
        #
        # instructions_json_response += json_schema_str

        self.json_response_instructions = instructions_json_response

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
        response_data = prompt_request_factory.request(text, llm_model)

        return text, response_data

    def generate_prompt_create_specification_summary(self, usr: str, llm_model: LLModel) -> (str, ResponseData):

        final_prompt = ("You are a systems engineer. Keep your response text only and as short as possible. "
                        "Summarize only the the important information that is required to specify the system, "
                        "its components and their connections from following user requirements "
                        "specification: " + usr)

        if self.offline_mode:

            response_data = ResponseData(response_str="No summary - Offline mode active...",
                                         input_tokens=15, output_tokens=15, time_seconds=5.0)

        else:

            # Send generated prompt as request
            response_data = prompt_request_factory.request(final_prompt, llm_model)

        return final_prompt, response_data

    def generate_prompt_create_abstract_model(self, system_description: str, llm_model: LLModel, save_to_disk: bool = True) -> (str, ResponseData):

        # Save for future correction prompts
        self._latest_specification_summary = system_description

        instructions_preface_file_path = PATH_DEFAULT_PROMPT_INSTRUCTIONS_PREFACE

        if instructions_preface_file_path.is_file():
            with open(instructions_preface_file_path, 'r') as file:
                instructions_preface: str = file.read()
        else:
            print(f"The file {instructions_preface_file_path} does not exist.")

        prompt = " The description: " + system_description + " "

        final_prompt = instructions_preface + prompt + self.system_modeling_instructions + self.json_response_instructions

        if self.offline_mode:

            with open(DEFAULT_ABSTRACT_MODEL_RESPONSE_PATH, 'r') as file:
                response: str = file.read()

            response_data = ResponseData(response_str=response,
                                         input_tokens=15, output_tokens=15, time_seconds=5.0)

        else:

            # Send generated prompt as request
            response_data = prompt_request_factory.request_as_function_call(final_prompt, llm_model)

            if save_to_disk:
                self._save_prompt_and_response_to_disk(final_prompt, response_data.response_str)

        return final_prompt, response_data

    def generate_prompt_improve_abstract_model_by_feedback(self, abstract_system_model_json: str, feedback: str,
                                                           llm_model: LLModel) -> (str, ResponseData):

        final_prompt = ("The following JSON contains a model of a system with its components and connections. "
                        + abstract_system_model_json
                        + " Improve this model and the json using the following instructions: "
                        + feedback)

        if self.offline_mode:

            with open(DEFAULT_ABSTRACT_MODEL_RESPONSE_PATH, 'r') as file:
                response: str = file.read()

            response_data = ResponseData(response_str=response,
                                         input_tokens=15, output_tokens=15, time_seconds=5.0)

        else:

            # Send generated prompt as request
            response_data = prompt_request_factory.request_as_function_call(final_prompt, llm_model)

        return final_prompt, response_data

    def generate_prompt_autocorrect_abstract_model(self, abstract_system_model_json: str, error: Exception,
                                                   llm_model: LLModel) -> (str, ResponseData):

        if isinstance(error, AbstractComponentError):
            auto_correct_instruction = ("There is a problem with a component. Correct the model based on this error message: "
                                        + error.message + ". Problem with the following components: "
                                        + str(error.list_wrong_components) + " ." + self.system_modeling_instructions
                                        + "Make sure that every component name excluding the '_' and number is in the "
                                          "list of possible components, if not, find the closest one and replace it.")

        elif isinstance(error, AbstractConnectionError):
            auto_correct_instruction = ("There is a problem with a connection. Correct the model based on this error message: "
                                        + error.message)

        else:
            return

        final_prompt = ("The following JSON contains a model of a system with its components and connections. "
                        + abstract_system_model_json
                        + " Improve this model and the json using the following instructions: "
                        + auto_correct_instruction)

        if self.offline_mode:

            with open(DEFAULT_ABSTRACT_MODEL_RESPONSE_PATH, 'r') as file:
                response: str = file.read()

            response_data = ResponseData(response_str=response,
                                         input_tokens=15, output_tokens=15, time_seconds=5.0)

        else:

            # Send generated prompt as request
            response_data = prompt_request_factory.request_as_function_call(final_prompt, llm_model)

        return final_prompt, response_data

    def generate_prompt_manual_autocorrection_abstract_model(self, abstract_system_model_json: str, llm_model: LLModel) -> (str, ResponseData):

        final_prompt = ("The following JSON contains a model of a system with its components and connections. "
                        + abstract_system_model_json
                        + " Analyse and improve this model and the json so that it exactly matches these specifications: "
                        + self._latest_specification_summary
                        + " . Are there any errors with this design? Will it function the way it is intended? "
                          "Is each component connected to at least two other components? Fix any errors. "
                        + self.system_modeling_instructions)

        if self.offline_mode:

            with open(DEFAULT_ABSTRACT_MODEL_RESPONSE_PATH, 'r') as file:
                response: str = file.read()

            response_data = ResponseData(response_str=response,
                                         input_tokens=15, output_tokens=15, time_seconds=5.0)

        else:

            # Send generated prompt as request
            response_data = prompt_request_factory.request_as_function_call(final_prompt, llm_model)

        return final_prompt, response_data
