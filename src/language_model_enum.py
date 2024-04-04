# -*- coding: utf-8 -*-

"""
Definition large language models that may be used to generate abstract system models.

Last modification: 04.04.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from enum import Enum, auto


class LLModel(Enum):
    OPENAI_GPT35_Turbo = auto()
    ANTHROPIC_CLAUDE3_OPUS = auto()
    ANTHROPIC_CLAUDE3_SONNET = auto()
    MISTRAL_MIXTRAL_8X7B = auto()
    META_LLAMA2_70B = auto()
    WIZARDLM_13B = auto()
    # OPENAI_GPT4_Turbo = auto()
    # OPENAI_GPT4 = auto()
    # GOOGLE_GEMINI = auto()
    # ALEPH_ALPHA_LUMINOUS = auto()
    # INFLECTION_25 = auto()
    # XAI_GROK = auto()

    @classmethod
    def from_str(cls, name: str):
        for model in list(cls):
            if model.name == name:
                return model
