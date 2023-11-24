# -*- coding: utf-8 -*-

"""
Response Interpreter

Last modification: 23.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from src.model.system import System
from src.utils.json_schema_validator import JSONSchemaValidator
from src.simscape.interface import SystemSimulinkAdapter, Implementer


class ResponseInterpreter:

    def __init__(self):
        self.json_validator = JSONSchemaValidator()
        self.interf = Implementer(SystemSimulinkAdapter)

    def interpret_json(self, json_data: dict):

        if not self.json_validator.is_valid_json_data(json_data):
            return

        # Prototyping: Create a new system, load from and save to json file
        system = System()
        system.load_from_json_data(json_data)
        system.save_as_json()

        # Create system model in simulink and save result to disk
        self.interf.input_to_simulink(system, system.name)
        self.interf.save_to_disk(system.name)

        print("Done.")
