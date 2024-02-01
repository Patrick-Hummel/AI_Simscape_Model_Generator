# -*- coding: utf-8 -*-

"""
Use of the "Factory Method" design pattern to create prompt requests to LLM APIs.

Last modification: 01.02.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from src.api_client import OpenAIGPTClient
from src.language_model_enum import LLModel
from src.model.response import ResponseData


def request(prompt: str, llm_model: LLModel) -> ResponseData:

    try:
        requester = get_requester(llm_model)
        return requester(prompt)

    except NotImplementedError as nie:
        print(f"Error: Request to {llm_model.name} not yet implemented.")
        return ResponseData()


def request_as_function_call(prompt: str, llm_model: LLModel) -> ResponseData:

    try:
        requester = get_requester_function_call(llm_model)
        return requester(prompt)

    except NotImplementedError as nie:
        print(f"Error: Request as function call to {llm_model.name} not yet implemented.")
        return ResponseData()


def get_requester(llm_model: LLModel):

    match llm_model:
        case LLModel.OPENAI_GPT35_Turbo: return _request_openai
        case LLModel.OPENAI_GPT4_Turbo: raise NotImplementedError()
        case LLModel.OPENAI_GPT4: raise NotImplementedError()
        case LLModel.GOOGLE_BARD: raise NotImplementedError()
        case LLModel.ANTHROPIC_CLAUDE2: raise NotImplementedError()
        case LLModel.ALEPH_ALPHA_LUMINOUS: raise NotImplementedError()
        case LLModel.META_LLAMA2: raise NotImplementedError()
        case LLModel.XAI_GROK: raise NotImplementedError()

        case _: raise ValueError(llm_model)


def get_requester_function_call(llm_model: LLModel):

    match llm_model:
        case LLModel.OPENAI_GPT35_Turbo: return _request_openai_as_function_call
        case LLModel.OPENAI_GPT4_Turbo: raise NotImplementedError()
        case LLModel.OPENAI_GPT4: raise NotImplementedError()
        case LLModel.GOOGLE_BARD: raise NotImplementedError()
        case LLModel.ANTHROPIC_CLAUDE2: raise NotImplementedError()
        case LLModel.ALEPH_ALPHA_LUMINOUS: raise NotImplementedError()
        case LLModel.META_LLAMA2: raise NotImplementedError()
        case LLModel.XAI_GROK: raise NotImplementedError()

        case _: raise ValueError(llm_model)


def _request_openai(prompt) -> ResponseData:
    client = OpenAIGPTClient()
    return client.request(prompt=prompt)


def _request_bard(prompt) -> ResponseData:
    raise NotImplementedError


def _request_openai_as_function_call(prompt) -> ResponseData:
    client = OpenAIGPTClient()
    return client.request_as_function_call(prompt=prompt)
