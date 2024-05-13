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
