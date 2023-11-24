# -*- coding: utf-8 -*-

"""
Use of the "Factory Method" design pattern to create prompt requests to LLM APIs.

Last modification: 23.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from src.api_client import OpenAIGPTClient
from config.gobal_constants import LLM_MODEL_OPENAI_GPT, LLM_MODEL_GOOGLE_BARD, LLM_MODEL_META_LLAMA2, \
    LLM_MODEL_ANTHROPIC_CLAUDE2, LLM_MODEL_XAI_GROK, LLM_MODEL_ALEPH_ALPHA_LUMINOUS


def request(prompt: str, llm_model: str):
    requester = get_requester(llm_model)
    return requester(prompt)


def get_requester(llm_model: str):
    if llm_model == LLM_MODEL_OPENAI_GPT:
        return _request_openai
    elif llm_model == LLM_MODEL_GOOGLE_BARD:
        return _request_bard
    elif llm_model == LLM_MODEL_META_LLAMA2:
        raise NotImplementedError
    elif llm_model == LLM_MODEL_ANTHROPIC_CLAUDE2:
        raise NotImplementedError
    elif llm_model == LLM_MODEL_XAI_GROK:
        raise NotImplementedError
    elif llm_model == LLM_MODEL_ALEPH_ALPHA_LUMINOUS:
        raise NotImplementedError
    else:
        raise ValueError(llm_model)


def _request_openai(prompt) -> str:
    client = OpenAIGPTClient()
    return client.request(prompt=prompt)


def _request_bard(prompt) -> str:
    raise NotImplementedError
