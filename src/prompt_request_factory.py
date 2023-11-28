# -*- coding: utf-8 -*-

"""
Use of the "Factory Method" design pattern to create prompt requests to LLM APIs.

Last modification: 28.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from src.api_client import OpenAIGPTClient
from src.language_model_enum import LLModel


def request(prompt: str, llm_model: LLModel):
    requester = get_requester(llm_model)
    return requester(prompt)


def get_requester(llm_model: LLModel):

    match llm_model:
        case LLModel.OPENAI_GPT35_Turbo: return _request_openai
        case LLModel.OPENAI_GPT4: return NotImplementedError()
        case LLModel.OPENAI_GPT4_Turbo: return NotImplementedError()
        case LLModel.GOOGLE_BARD: return NotImplementedError()
        case LLModel.META_LLAMA2: return NotImplementedError()
        case LLModel.ANTHROPIC_CLAUDE2: return NotImplementedError()
        case LLModel.XAI_GROK: return NotImplementedError()
        case LLModel.ALEPH_ALPHA_LUMINOUS: return NotImplementedError()
        case _: raise ValueError(llm_model)


def _request_openai(prompt) -> str:
    client = OpenAIGPTClient()
    # return client.request(prompt=prompt)
    return client.request_as_function_call(prompt=prompt)


def _request_bard(prompt) -> str:
    raise NotImplementedError
