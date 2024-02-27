# -*- coding: utf-8 -*-

"""
Definition large language models that may be used to generate abstract system models.

Last modification: 27.02.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from enum import Enum, auto


class LLModel(Enum):
    OPENAI_GPT35_Turbo = auto()
    OPENAI_GPT4_Turbo = auto()
    OPENAI_GPT4 = auto()
    GOOGLE_GEMINI = auto()
    ANTHROPIC_CLAUDE2 = auto()
    ALEPH_ALPHA_LUMINOUS = auto()
    META_LLAMA2 = auto()
    XAI_GROK = auto()

    @classmethod
    def from_str(cls, name: str):
        for model in list(cls):
            if model.name == name:
                return model
