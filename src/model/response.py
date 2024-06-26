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

A class representing a response from a large language model.

Last modification: 01.02.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from dataclasses import dataclass


@dataclass
class ResponseData:

    response_str: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    time_seconds: float = 0.0
    model_name: str = ""
