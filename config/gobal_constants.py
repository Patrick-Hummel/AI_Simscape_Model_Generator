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

Definition of global constants.

Last modification: 04.04.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from pathlib import Path


MATLAB_DEFAULT_SOLVER = "ode23t"
MATLAB_DEFAULT_STOP_TIME = 100

PATH_DEFAULT_DATA_JSON = Path("data/json")
PATH_DEFAULT_SYSTEM_OUTPUT_JSON = Path("data/json/output")
PATH_DEFAULT_SIMSCAPE_MODEL_OUTPUT_SLX = Path("data/simscape/output")
PATH_DEFAULT_JSON_SCHEMA_FILE = Path("data/json/system_model_schema.json")

PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE = Path("data/json/abstract_model/abstract_system_model_schema.json")
PATH_DEFAULT_ABSTRACT_SYSTEM_EXAMPLE_JSON_FILE = Path("data/json/abstract_model/example_abstract_system_1.json")

PATH_DEFAULT_LAST_GENERATED_PROMPT_TXT_FILE = Path("data/prompts/last_generated_prompt.txt")

PATH_DEFAULT_RESPONSES_DIR = Path("data/responses")

PATH_EXAMPLE_USER_SPECIFICATION = Path("data/examples/urs_example.txt")

OPENAI_GPT35_TURBO_INPUT_TOKENS_COST_USD_PER_1K = 0.0010
OPENAI_GPT35_TURBO_OUTPUT_TOKENS_COST_USD_PER_1K = 0.0020
