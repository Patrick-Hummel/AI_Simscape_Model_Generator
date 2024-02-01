# -*- coding: utf-8 -*-

"""
A class

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
