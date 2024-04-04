# -*- coding: utf-8 -*-

"""
Use of the "Singleton" design pattern to only allow single instances of API clients for prompt requests.

Singleton metaclass solution inspired by the answer of user "WorldSEnder" on Stack Overflow (07.07.2015):
https://stackoverflow.com/questions/31269974/why-singleton-in-python-calls-init-multiple-times-and-how-to-avoid-it
Answer: https://stackoverflow.com/a/31270973 User: https://stackoverflow.com/users/3102935/worldsender


Last modification: 04.04.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import json
import os
from time import time

from anthropic import Anthropic
from openai import OpenAI

from config.gobal_constants import PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE
from src.model.response import ResponseData


OPENAI_GPT35_Turbo = "gpt-3.5-turbo-0125"
OPENAI_GPT34_Turbo_Previous = "gpt-3.5-turbo-1106"

MODEL_META_LLAMA_2_70B = "meta-llama/Llama-2-70b-chat-hf"
MODEL_MISTRAL_MIXTRAL_8X7B = "mistralai/Mixtral-8x7B-Instruct-v0.1"
MODEL_WIZARDLM_13B = "WizardLM/WizardLM-13B-V1.2"

ANTHROPIC_CLAUDE3_OPUS_MODEL_NAME = "claude-3-opus-20240229"
ANTHROPIC_CLAUDE3_SONNET_MODEL_NAME = "claude-3-sonnet-20240229"
ANTHROPIC_CLAUDE3_HAIKU_MODEL_NAME = "claude-3-haiku-20240229"


class Singleton(type):
    def __init__(self, name, bases, mmbs):
        super(Singleton, self).__init__(name, bases, mmbs)
        self._instance = super(Singleton, self).__call__()

    def __call__(self, *args, **kw):
        return self._instance


class OpenAIGPTClient(metaclass=Singleton):

    def __init__(self):
        self.client = OpenAI()
        print("-> OpenAI API client created")

        # Load JSON schema and prepare to be added to function call parameter
        with open(PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE, 'r') as file:
            self.json_response_schema = json.load(file)

        self.json_response_schema.pop('$schema', None)

    def request(self, prompt: str, temperature: float = 1.0) -> ResponseData:

        start_time = time()

        # Request a valid json as response format
        completion = self.client.chat.completions.create(
            model=OPENAI_GPT35_Turbo,
            # response_format={"type": "json_object"},
            temperature=temperature,
            messages=[
                {"role": "system",
                 "content": "You are an electrical engineer."},
                {"role": "user", "content": prompt}
            ]
        )

        print(f"Tokens (Response): Prompt = {completion.usage.prompt_tokens}, "
              f"Completion = {completion.usage.completion_tokens}, "
              f"Total = {completion.usage.total_tokens}")

        response_data = ResponseData(response_str=completion.choices[0].message.content,
                                     input_tokens=completion.usage.prompt_tokens,
                                     output_tokens=completion.usage.completion_tokens,
                                     time_seconds=time() - start_time)

        return response_data

    def request_as_function_call(self, prompt: str, temperature: float = 1.0) -> ResponseData:

        start_time = time()

        # Request a valid json as response format
        completion = self.client.chat.completions.create(
            model=OPENAI_GPT35_Turbo,
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            tools=[{"type": "function", "function": {"name": "createSystemModelObject", "parameters": self.json_response_schema}}],
            tool_choice={"type": "function", "function": {"name": "createSystemModelObject"}}

            # Parameter 'function_call' is being deprecated (new: tool_choice)
            # function_call={"name": "createSystemModelObject"}
            # functions = [
            #     {
            #         "name": "createSystemModelObject",
            #         "parameters": self.json_response_schema
            #     }
            # ],
        )

        print(f"Tokens (Response): Prompt = {completion.usage.prompt_tokens}, "
              f"Completion = {completion.usage.completion_tokens}, "
              f"Total = {completion.usage.total_tokens}")

        response_data = ResponseData(response_str=completion.choices[0].message.tool_calls[0].function.arguments,    # function_call.arguments,
                                     input_tokens=completion.usage.prompt_tokens,
                                     output_tokens=completion.usage.completion_tokens,
                                     time_seconds=time() - start_time)

        return response_data


class TogetherAPIClient(metaclass=Singleton):

    def __init__(self):

        TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")

        self.client = OpenAI(
            api_key=TOGETHER_API_KEY,
            base_url='https://api.together.xyz/v1'
        )
        print("-> Together (OpenAI) API client created")

        # Load JSON schema and prepare to be added to function call parameter
        with open(PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE, 'r') as file:
            self.json_response_schema = json.load(file)

        self.json_response_schema.pop('$schema', None)

    def request(self, prompt: str, temperature: float = 1.0, model_name: str = MODEL_MISTRAL_MIXTRAL_8X7B) -> ResponseData:

        start_time = time()

        # Request a valid json as response format
        completion = self.client.chat.completions.create(
            model=model_name,
            # response_format={"type": "json_object"},
            temperature=temperature,
            messages=[
                {"role": "system",
                 "content": "You are an electrical engineer."},
                {"role": "user", "content": prompt}
            ]
        )

        print(f"Tokens (Response): Prompt = {completion.usage.prompt_tokens}, "
              f"Completion = {completion.usage.completion_tokens}, "
              f"Total = {completion.usage.total_tokens}")

        response_data = ResponseData(response_str=completion.choices[0].message.content,
                                     input_tokens=completion.usage.prompt_tokens,
                                     output_tokens=completion.usage.completion_tokens,
                                     time_seconds=time() - start_time)

        return response_data

    def request_as_function_call(self, prompt: str, temperature: float = 1.0, model_name: str = MODEL_META_LLAMA_2_70B) -> ResponseData:

        start_time = time()

        # Request a valid json as response format
        completion = self.client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            tools=[{"type": "function", "function": {"name": "createSystemModelObject", "parameters": self.json_response_schema}}],
            tool_choice={"type": "function", "function": {"name": "createSystemModelObject"}}

            # Parameter 'function_call' is being deprecated (new: tool_choice)
            # function_call={"name": "createSystemModelObject"}
            # functions = [
            #     {
            #         "name": "createSystemModelObject",
            #         "parameters": self.json_response_schema
            #     }
            # ],
        )

        print(f"Tokens (Response): Prompt = {completion.usage.prompt_tokens}, "
              f"Completion = {completion.usage.completion_tokens}, "
              f"Total = {completion.usage.total_tokens}")

        response_data = ResponseData(response_str=completion.choices[0].message.tool_calls[0].function.arguments,    # function_call.arguments,
                                     input_tokens=completion.usage.prompt_tokens,
                                     output_tokens=completion.usage.completion_tokens,
                                     time_seconds=time() - start_time)

        return response_data


class AnthropicAPIClient(metaclass=Singleton):

    def __init__(self):

        ANTHROPIC_API_KEY = os.environ.get("ANTRHOPIC_API_KEY")

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        print("-> Anthropic API client created")

        # Load JSON schema and prepare to be added to function call parameter
        with open(PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE, 'r') as file:
            self.json_response_schema = json.load(file)

        self.json_response_schema.pop('$schema', None)

    def request(self, prompt: str, temperature: float = 1.0, model_name: str = ANTHROPIC_CLAUDE3_OPUS_MODEL_NAME) -> ResponseData:

        start_time = time()

        completion = self.client.messages.create(
            model=model_name,
            max_tokens=2048,
            messages=[{
                        "role": "user",
                        "content": prompt
                    }]
        )

        print(f"Tokens (Response): Prompt = {completion.usage.input_tokens}, "
              f"Completion = {completion.usage.output_tokens}, "
              f"Total = {completion.usage.input_tokens + completion.usage.output_tokens}")

        response_data = ResponseData(response_str=completion.content[0].text,
                                     input_tokens=completion.usage.input_tokens,
                                     output_tokens=completion.usage.output_tokens,
                                     time_seconds=time() - start_time)

        return response_data

    def request_as_function_call(self, prompt: str, temperature: float = 1.0, model_name: str = MODEL_META_LLAMA_2_70B) -> ResponseData:

        start_time = time()

        # Request a valid json as response format
        completion = self.client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            tools=[{"type": "function", "function": {"name": "createSystemModelObject", "parameters": self.json_response_schema}}],
            tool_choice={"type": "function", "function": {"name": "createSystemModelObject"}}

            # Parameter 'function_call' is being deprecated (new: tool_choice)
            # function_call={"name": "createSystemModelObject"}
            # functions = [
            #     {
            #         "name": "createSystemModelObject",
            #         "parameters": self.json_response_schema
            #     }
            # ],
        )

        print(f"Tokens (Response): Prompt = {completion.usage.prompt_tokens}, "
              f"Completion = {completion.usage.completion_tokens}, "
              f"Total = {completion.usage.total_tokens}")

        response_data = ResponseData(response_str=completion.choices[0].message.tool_calls[0].function.arguments,    #function_call.arguments,
                                     input_tokens=completion.usage.prompt_tokens,
                                     output_tokens=completion.usage.completion_tokens,
                                     time_seconds=time() - start_time)

        return response_data
