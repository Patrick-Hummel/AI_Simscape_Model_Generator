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

Use of the "Singleton" design pattern to only allow single instances of API clients for prompt requests.

Singleton metaclass solution inspired by the answer of user "WorldSEnder" on Stack Overflow (07.07.2015):
https://stackoverflow.com/questions/31269974/why-singleton-in-python-calls-init-multiple-times-and-how-to-avoid-it
Answer: https://stackoverflow.com/a/31270973 User: https://stackoverflow.com/users/3102935/worldsender


Last modification: 07.04.2024
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

# -- OPENAI --
OPENAI_GPT35_TURBO = "gpt-3.5-turbo-0125"
OPENAI_GPT34_TURBO_PREVIOUS = "gpt-3.5-turbo-1106"

# -- TOGETHER AI --
META_LLAMA_2_70B = "meta-llama/Llama-2-70b-chat-hf"
MISTRAL_MIXTRAL_8X7B = "mistralai/Mixtral-8x7B-Instruct-v0.1"
WIZARDLM_13B = "WizardLM/WizardLM-13B-V1.2"

# -- ANTHROPIC --
ANTHROPIC_CLAUDE3_OPUS_MODEL_NAME = "claude-3-opus-20240229"
ANTHROPIC_CLAUDE3_SONNET_MODEL_NAME = "claude-3-sonnet-20240229"
ANTHROPIC_CLAUDE3_HAIKU_MODEL_NAME = "claude-3-haiku-20240229"
ANTHROPIC_MAX_TOKENS = 2048

# -- Cost calculation --
MODEL_PRICES_USD_PER_TOKEN_APRIL_2024_DICT = {
    ANTHROPIC_CLAUDE3_OPUS_MODEL_NAME: {"input": 15/1e6, "output": 75/1e6},
    ANTHROPIC_CLAUDE3_SONNET_MODEL_NAME: {"input": 3/1e6, "output": 15/1e6},
    ANTHROPIC_CLAUDE3_HAIKU_MODEL_NAME: {"input": 0.25/1e6, "output": 1.25/1e6},
    OPENAI_GPT35_TURBO: {"input": 0.5 / 1e6, "output": 1.5 / 1e6},
    META_LLAMA_2_70B: {"input": 0.9 / 1e6, "output": 0.9 / 1e6},
    MISTRAL_MIXTRAL_8X7B: {"input": 0.6 / 1e6, "output": 0.6 / 1e6},
    WIZARDLM_13B: {"input": 0.3 / 1e6, "output": 0.3 / 1e6}
}


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

    def request(self, prompt: str, temperature: float = 1.0, model_name: str = OPENAI_GPT35_TURBO) -> ResponseData:

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

        response_data = ResponseData(response_str=completion.choices[0].message.content,
                                     input_tokens=completion.usage.prompt_tokens,
                                     output_tokens=completion.usage.completion_tokens,
                                     time_seconds=time() - start_time,
                                     model_name=model_name)

        print_token_count_and_cost(response_data)

        return response_data

    def request_as_function_call(self, prompt: str, temperature: float = 1.0, model_name: str = OPENAI_GPT35_TURBO) -> ResponseData:

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
        )

        response_data = ResponseData(response_str=completion.choices[0].message.tool_calls[0].function.arguments,
                                     input_tokens=completion.usage.prompt_tokens,
                                     output_tokens=completion.usage.completion_tokens,
                                     time_seconds=time() - start_time,
                                     model_name=model_name)

        print_token_count_and_cost(response_data)

        return response_data


class TogetherAPIClient(metaclass=Singleton):

    def __init__(self):

        TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")

        self.client = OpenAI(
            api_key=TOGETHER_API_KEY,
            base_url='https://api.together.xyz/v1'
        )
        print("-> Together AI API client created")

        # Load JSON schema and prepare to be added to function call parameter
        with open(PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE, 'r') as file:
            self.json_response_schema = json.load(file)

        self.json_response_schema.pop('$schema', None)

    def request(self, prompt: str, temperature: float = 1.0, model_name: str = MISTRAL_MIXTRAL_8X7B) -> ResponseData:

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

        response_data = ResponseData(response_str=completion.choices[0].message.content,
                                     input_tokens=completion.usage.prompt_tokens,
                                     output_tokens=completion.usage.completion_tokens,
                                     time_seconds=time() - start_time,
                                     model_name=model_name)

        print_token_count_and_cost(response_data)

        return response_data

    def request_as_function_call(self, prompt: str, temperature: float = 1.0, model_name: str = META_LLAMA_2_70B) -> ResponseData:

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

        )

        response_data = ResponseData(response_str=completion.choices[0].message.tool_calls[0].function.arguments,
                                     input_tokens=completion.usage.prompt_tokens,
                                     output_tokens=completion.usage.completion_tokens,
                                     time_seconds=time() - start_time,
                                     model_name=model_name)

        print_token_count_and_cost(response_data)

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
            max_tokens=ANTHROPIC_MAX_TOKENS,
            temperature=temperature,
            messages=[{
                        "role": "user",
                        "content": prompt
                    }]
        )

        response_data = ResponseData(response_str=completion.content[0].text,
                                     input_tokens=completion.usage.input_tokens,
                                     output_tokens=completion.usage.output_tokens,
                                     time_seconds=time() - start_time,
                                     model_name=model_name)

        print_token_count_and_cost(response_data)

        return response_data

    def request_as_function_call(self, prompt: str, temperature: float = 1.0, model_name: str = ANTHROPIC_CLAUDE3_OPUS_MODEL_NAME) -> ResponseData:

        start_time = time()

        completion = self.client.beta.tools.messages.create(
            model=model_name,
            max_tokens=ANTHROPIC_MAX_TOKENS,
            temperature=temperature,
            tools=[
                {
                    "name": "createSystemModelObject",
                    "description": "Creates a model of a system, specifically an electrical circuit, "
                                   "based on the provided components and connections between the components.",
                    "input_schema": self.json_response_schema,
                }
            ],
            messages=[{
                "role": "user",
                "content": prompt
            }],
        )

        response_str = ""

        for content in completion.content:

            if content.type == "tool_use" and content.name == "createSystemModelObject":

                # Workaround for Sonnet (actual JSON in "properties")
                if model_name == ANTHROPIC_CLAUDE3_SONNET_MODEL_NAME and "properties" in content.input:
                    content.input = content.input["properties"]

                # This response is already in the form of a dictionary, however for capability this is converted
                # to a JSON string. In the future, the dictionary might be used directly.
                response_str = json.dumps(content.input)
                break

        response_data = ResponseData(response_str=response_str,
                                     input_tokens=completion.usage.input_tokens,
                                     output_tokens=completion.usage.output_tokens,
                                     time_seconds=time() - start_time,
                                     model_name=model_name)

        print_token_count_and_cost(response_data)

        return response_data


def token_cost_calculation(input_tokens: int, output_tokens: int, model_name: str) -> (float, float):

    if not model_name in MODEL_PRICES_USD_PER_TOKEN_APRIL_2024_DICT:
        raise ValueError(f"Please define price per input/output token of {model_name}")

    prices = MODEL_PRICES_USD_PER_TOKEN_APRIL_2024_DICT[model_name]

    input_token_cost = input_tokens * prices["input"]
    output_token_cost = output_tokens * prices["output"]

    return input_token_cost, output_token_cost


def print_token_count_and_cost(response_data: ResponseData) -> None:

    # Calculate cost of response
    input_cost, output_cost = token_cost_calculation(input_tokens=response_data.input_tokens,
                                                     output_tokens=response_data.output_tokens,
                                                     model_name=response_data.model_name)

    print(f"\n[MODEL: {response_data.model_name}\n"
          f"Input tokens: {response_data.input_tokens} -> USD {input_cost:.5f} \n"
          f"Output tokens: {response_data.output_tokens} -> USD {output_cost:.5f} \n"
          f"Total = {response_data.input_tokens + response_data.output_tokens} -> USD {input_cost + output_cost:.5f} \n"
          f"Response time: {response_data.time_seconds:.3f} s]")
