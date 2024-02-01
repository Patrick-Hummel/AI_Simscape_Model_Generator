# -*- coding: utf-8 -*-

"""
Main Window of the AI Simscape Model Generation tool.

Last modification: 01.02.2024
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
    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)


class IllegalStateTransitionError(Exception):
    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)
