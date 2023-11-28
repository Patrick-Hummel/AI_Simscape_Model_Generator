# -*- coding: utf-8 -*-

"""
Definition large language models that may be used to generate abstract system models.

Last modification: 28.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from enum import Enum, auto


class LLModel(Enum):
    OPENAI_GPT35_Turbo = auto()
    OPENAI_GPT4 = auto()
    OPENAI_GPT4_Turbo = auto()
    GOOGLE_BARD = auto()
    META_LLAMA2 = auto()
    ANTHROPIC_CLAUDE2 = auto()
    XAI_GROK = auto()
    ALEPH_ALPHA_LUMINOUS = auto()
