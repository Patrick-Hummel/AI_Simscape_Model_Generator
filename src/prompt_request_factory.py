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

Use of the "Factory Method" design pattern to create prompt requests to LLM APIs.

Last modification: 07.04.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from src.api_client import OpenAIGPTClient, TogetherAPIClient, META_LLAMA_2_70B, WIZARDLM_13B, \
    MISTRAL_MIXTRAL_8X7B, AnthropicAPIClient, ANTHROPIC_CLAUDE3_OPUS_MODEL_NAME, \
    ANTHROPIC_CLAUDE3_SONNET_MODEL_NAME, OPENAI_GPT35_TURBO

from src.language_model_enum import LLModel
from src.model.response import ResponseData


def request(prompt: str, llm_model: LLModel, temperature: float = 1.0) -> ResponseData:

    try:
        requester = get_requester(llm_model=llm_model)
        return requester(prompt=prompt, temperature=temperature)

    except NotImplementedError as nie:
        print(f"Error: Request to {llm_model.name} not yet implemented.")
        return ResponseData()


def request_as_function_call(prompt: str, llm_model: LLModel, temperature: float = 1.0) -> ResponseData:

    try:
        requester = get_requester_function_call(llm_model=llm_model)
        return requester(prompt=prompt, temperature=temperature)

    except NotImplementedError as nie:
        print(f"Error: Request as function call to {llm_model.name} not yet implemented.")
        return ResponseData()


def get_requester(llm_model: LLModel):

    match llm_model:
        case LLModel.OPENAI_GPT35_Turbo: return _request_openai_gpt35_turbo
        case LLModel.ANTHROPIC_CLAUDE3_OPUS: return _request_anthropic_claude3_opus
        case LLModel.ANTHROPIC_CLAUDE3_SONNET: return _request_anthropic_claude3_sonnet
        case LLModel.MISTRAL_MIXTRAL_8X7B: return _request_mixtral_8x7b
        case LLModel.META_LLAMA2_70B: return _request_meta_llama2_70b
        case LLModel.WIZARDLM_13B: return _request_wizardlm_13b

        case _: raise ValueError(llm_model)


def get_requester_function_call(llm_model: LLModel):

    match llm_model:
        case LLModel.OPENAI_GPT35_Turbo: return _request_openai_gpt35_turbo_as_function_call
        case LLModel.ANTHROPIC_CLAUDE3_OPUS: return _request_anthropic_claude3_opus_as_function_call
        case LLModel.ANTHROPIC_CLAUDE3_SONNET: return _request_anthropic_claude3_sonnet_as_function_call
        case LLModel.META_LLAMA2_70B: raise NotImplementedError()
        case LLModel.MISTRAL_MIXTRAL_8X7B: return _request_mixtral_8x7b_as_function_call
        case LLModel.WIZARDLM_13B: raise NotImplementedError()

        case _: raise ValueError(llm_model)


# -- OPENAI --
def _request_openai_gpt35_turbo(prompt: str, temperature: float) -> ResponseData:
    client = OpenAIGPTClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=OPENAI_GPT35_TURBO)


def _request_openai_gpt35_turbo_as_function_call(prompt: str, temperature: float) -> ResponseData:
    client = OpenAIGPTClient()
    return client.request_as_function_call(prompt=prompt, temperature=temperature, model_name=OPENAI_GPT35_TURBO)


# -- ANTHROPIC --
def _request_anthropic_claude3_opus(prompt: str, temperature: float) -> ResponseData:
    client = AnthropicAPIClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=ANTHROPIC_CLAUDE3_OPUS_MODEL_NAME)


def _request_anthropic_claude3_opus_as_function_call(prompt: str, temperature: float) -> ResponseData:
    client = AnthropicAPIClient()
    return client.request_as_function_call(prompt=prompt, temperature=temperature, model_name=ANTHROPIC_CLAUDE3_OPUS_MODEL_NAME)


def _request_anthropic_claude3_sonnet(prompt: str, temperature: float) -> ResponseData:
    client = AnthropicAPIClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=ANTHROPIC_CLAUDE3_SONNET_MODEL_NAME)


def _request_anthropic_claude3_sonnet_as_function_call(prompt: str, temperature: float) -> ResponseData:
    client = AnthropicAPIClient()
    return client.request_as_function_call(prompt=prompt, temperature=temperature, model_name=ANTHROPIC_CLAUDE3_SONNET_MODEL_NAME)


# -- MISTRAL AI --
def _request_mixtral_8x7b(prompt: str, temperature: float) -> ResponseData:
    client = TogetherAPIClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=MISTRAL_MIXTRAL_8X7B)


def _request_mixtral_8x7b_as_function_call(prompt: str, temperature: float) -> ResponseData:
    client = TogetherAPIClient()
    return client.request_as_function_call(prompt=prompt, temperature=temperature, model_name=MISTRAL_MIXTRAL_8X7B)


# -- META --
def _request_meta_llama2_70b(prompt: str, temperature: float) -> ResponseData:
    client = TogetherAPIClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=META_LLAMA_2_70B)


# -- WIZARDLM --
def _request_wizardlm_13b(prompt: str, temperature: float) -> ResponseData:
    client = TogetherAPIClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=WIZARDLM_13B)
