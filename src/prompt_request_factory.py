# -*- coding: utf-8 -*-

"""
Use of the "Factory Method" design pattern to create prompt requests to LLM APIs.

Last modification: 04.04.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from src.api_client import OpenAIGPTClient, TogetherAPIClient, MODEL_META_LLAMA_2_70B, MODEL_WIZARDLM_13B, \
    MODEL_MISTRAL_MIXTRAL_8X7B, AnthropicAPIClient, ANTHROPIC_CLAUDE3_OPUS_MODEL_NAME, \
    ANTHROPIC_CLAUDE3_SONNET_MODEL_NAME
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
        case LLModel.OPENAI_GPT35_Turbo: return _request_openai
        case LLModel.ANTHROPIC_CLAUDE3_OPUS: return _request_anthropic_claude3_opus
        case LLModel.ANTHROPIC_CLAUDE3_SONNET: return _request_anthropic_claude3_sonnet
        case LLModel.MISTRAL_MIXTRAL_8X7B: return _request_mixtral_8x7B
        case LLModel.META_LLAMA2_70B: return _request_meta_llama2_70B
        case LLModel.WIZARDLM_13B: return _request_wizardlm_13B

        case _: raise ValueError(llm_model)


def get_requester_function_call(llm_model: LLModel):

    match llm_model:
        case LLModel.OPENAI_GPT35_Turbo: return _request_openai_as_function_call
        case LLModel.ANTHROPIC_CLAUDE3_OPUS: raise NotImplementedError()
        case LLModel.ANTHROPIC_CLAUDE3_SONNET: raise NotImplementedError()
        case LLModel.META_LLAMA2_70B: raise NotImplementedError()
        case LLModel.MISTRAL_MIXTRAL_8X7B: return _request_mixtral_8x7B_as_function_call
        case LLModel.WIZARDLM_13B: raise NotImplementedError()

        case _: raise ValueError(llm_model)


def _request_openai(prompt: str, temperature: float) -> ResponseData:
    client = OpenAIGPTClient()
    return client.request(prompt=prompt, temperature=temperature)


def _request_mixtral_8x7B(prompt: str, temperature: float) -> ResponseData:
    client = TogetherAPIClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=MODEL_MISTRAL_MIXTRAL_8X7B)


def _request_meta_llama2_70B(prompt: str, temperature: float) -> ResponseData:
    client = TogetherAPIClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=MODEL_META_LLAMA_2_70B)


def _request_wizardlm_13B(prompt: str, temperature: float) -> ResponseData:
    client = TogetherAPIClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=MODEL_WIZARDLM_13B)


def _request_anthropic_claude3_opus(prompt: str, temperature: float) -> ResponseData:
    client = AnthropicAPIClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=ANTHROPIC_CLAUDE3_OPUS_MODEL_NAME)


def _request_anthropic_claude3_sonnet(prompt: str, temperature: float) -> ResponseData:
    client = AnthropicAPIClient()
    return client.request(prompt=prompt, temperature=temperature, model_name=ANTHROPIC_CLAUDE3_SONNET_MODEL_NAME)


def _request_openai_as_function_call(prompt: str, temperature: float) -> ResponseData:
    client = OpenAIGPTClient()
    return client.request_as_function_call(prompt=prompt, temperature=temperature)


def _request_mixtral_8x7B_as_function_call(prompt: str, temperature: float) -> ResponseData:
    client = TogetherAPIClient()
    return client.request_as_function_call(prompt=prompt, temperature=temperature, model_name=MODEL_MISTRAL_MIXTRAL_8X7B)
