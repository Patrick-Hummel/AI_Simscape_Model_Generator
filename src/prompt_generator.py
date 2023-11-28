# -*- coding: utf-8 -*-

"""
Prompt Generator

Last modification: 28.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import tiktoken

from config.gobal_constants import PATH_DEFAULT_JSON_SCHEMA_FILE, PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE, \
    PATH_DEFAULT_LAST_GENERATED_PROMPT_TXT_FILE, PATH_DEFAULT_PROMPT_INSTRUCTIONS_JSON_RESPONSE, \
    PATH_DEFAULT_PROMPT_INSTRUCTIONS_PREFACE
from src.abstract_model.abstract_components import AbstractComponent


class PromptGenerator:

    def __init__(self):
        self.system_modeling_instructions = ""
        self.json_response_instructions = ""

        self.create_system_modeling_instructions()
        self.create_json_response_instructions()

    def create_system_modeling_instructions(self):

        implemented_abstract_component_types_dict = AbstractComponent.get_implemented_component_types_dict()

        instructions = "Only the following components may be used: "

        for component in implemented_abstract_component_types_dict.keys():
            instructions += f"{component}, "

        self.system_modeling_instructions += instructions

    def create_json_response_instructions(self):

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

    def generate_prompt(self, system_description: str, save_to_disk: bool = True) -> str:

        instructions_preface_file_path = PATH_DEFAULT_PROMPT_INSTRUCTIONS_PREFACE

        if instructions_preface_file_path.is_file():
            with open(instructions_preface_file_path, 'r') as file:
                instructions_preface: str = file.read()
        else:
            print(f"The file {instructions_preface_file_path} does not exist.")

        prompt = " The description: " + system_description + " "

        final_prompt = instructions_preface + prompt + self.system_modeling_instructions + self.json_response_instructions

        if save_to_disk:
            with open(PATH_DEFAULT_LAST_GENERATED_PROMPT_TXT_FILE, 'w') as file:
                file.write(final_prompt)
            print("-> Prompt saved to file.")

        # encoding = tiktoken.get_encoding("cl100k_base")
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(final_prompt))
        input_token_price_usd = (num_tokens / 1000) * 0.0010

        print(f"-> Token count of prompt: {num_tokens} (min. expected cost: $ {input_token_price_usd})")

        return final_prompt
