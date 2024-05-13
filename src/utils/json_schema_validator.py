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

This class validates JSON files or JSON data in the form of dictionary objects based on a predefined JSON schema.

Last modification: 28.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import json
from jsonschema import validate, ValidationError
from pathlib import Path


class JSONSchemaValidator:

    def __init__(self, json_schema_filepath: Path):

        try:

            # Convert Path to string before using json.loads
            with open(str(json_schema_filepath), 'r') as file:
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
