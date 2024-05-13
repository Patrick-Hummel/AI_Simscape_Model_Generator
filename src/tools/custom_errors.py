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

Main Window of the AI Simscape Model Generation tool.

Last modification: 04.04.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"


class JSONSchemaError(Exception):
    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)


class AbstractComponentError(Exception):
    def __init__(self, message: str = "", list_wrong_components: list = None):
        self.message = message

        if list_wrong_components is None:
            list_wrong_components = []

        self.list_wrong_components = list_wrong_components

        super().__init__(self.message)


class AbstractConnectionError(Exception):
    def __init__(self, message="", list_wrong_connections: list = None):
        self.message = message

        if list_wrong_connections is None:
            list_wrong_connections = []

        self.list_wrong_connections = list_wrong_connections

        super().__init__(self.message)


class IllegalStateTransitionError(Exception):
    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)
