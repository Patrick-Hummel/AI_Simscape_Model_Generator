# -*- coding: utf-8 -*-

"""
Definition of global constants.

Last modification: 23.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from pathlib import Path

# TODO Use enum instead of string constants
LLM_MODEL_OPENAI_GPT = "openai"
LLM_MODEL_GOOGLE_BARD = "bard"
LLM_MODEL_META_LLAMA2 = "llama2"
LLM_MODEL_ANTHROPIC_CLAUDE2 = "claude2"
LLM_MODEL_XAI_GROK = "grok"
LLM_MODEL_ALEPH_ALPHA_LUMINOUS = "luminous"

MATLAB_DEFAULT_SOLVER = "ode23t"
MATLAB_DEFAULT_STOP_TIME = 100

PATH_DEFAULT_DATA_JSON = Path("data/json")
PATH_DEFAULT_SYSTEM_OUTPUT_JSON = Path("data/json/output")
PATH_DEFAULT_SIMSCAPE_MODEL_OUTPUT_SLX = Path("data/simscape/output")
PATH_DEFAULT_JSON_SCHEMA_FILE = Path("data/json/system_model_schema.json")
