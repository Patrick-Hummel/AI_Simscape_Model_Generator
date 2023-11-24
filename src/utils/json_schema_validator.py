# -*- coding: utf-8 -*-

"""
This class validates JSON files or JSON data in the form of dictionary objects based on a predefined JSON schema.

Last modification: 23.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import json
from jsonschema import validate, ValidationError
from pathlib import Path

from config.gobal_constants import PATH_DEFAULT_JSON_SCHEMA_FILE


class JSONSchemaValidator:

    def __init__(self):

        try:

            # Convert Path to string before using json.loads
            with open(str(PATH_DEFAULT_JSON_SCHEMA_FILE), 'r') as file:
                self.json_schema = json.load(file)

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON schema: {e}")
            exit(1)

    def is_valid_json_file(self, path_to_json: Path) -> bool:

        try:

            # Convert Path to string before using json.loads
            with open(str(path_to_json), 'r') as file:
                json_data = json.load(file)

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")
            exit(1)

        return self.is_valid_json_data(json_data)

    def is_valid_json_data(self, json_data: dict) -> bool:

        # Prove that it is valid
        is_valid_json = False

        # Validate the JSON data against the schema
        try:

            validate(instance=json_data, schema=self.json_schema)
            print("JSON is valid against the schema.")
            is_valid_json = True

        except ValidationError as e:
            print(f"JSON validation failed: {e}")

        return is_valid_json
