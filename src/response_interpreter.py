# -*- coding: utf-8 -*-

"""
Response Interpreter

Last modification: 28.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import json
from datetime import datetime

from config.gobal_constants import (PATH_DEFAULT_JSON_SCHEMA_FILE, PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE,
                                    PATH_DEFAULT_RESPONSES_DIR, PATH_DEFAULT_ABSTRACT_SYSTEM_EXAMPLE_JSON_FILE)

from src.abstract_model.abstract_system import AbstractSystem
from src.utils.json_schema_validator import JSONSchemaValidator

USE_EXISTING_JSON = False


class ResponseInterpreter:

    def __init__(self):
        self.json_validator = JSONSchemaValidator(PATH_DEFAULT_JSON_SCHEMA_FILE)
        self.abstract_model_json_validator = JSONSchemaValidator(PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE)

    def interpret_response(self, response: str, save_to_disk: bool = True) -> AbstractSystem:

        json_data = {}

        # Parse the response as JSON
        try:
            json_data = json.loads(response)
            print("JSON object extracted successfully:")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

        if save_to_disk:

            # Save complete response (debugging)
            datetime_now = datetime.now()
            datetime_now_str = datetime_now.strftime("%Y%m%d_%H%M")

            path_output_dir = PATH_DEFAULT_RESPONSES_DIR / f"api_call_{datetime_now_str}"

            if not path_output_dir.is_dir():
                path_output_dir.mkdir(parents=True)

            response_file = path_output_dir / f"response_{datetime_now_str}.txt"
            with open(response_file, 'w') as file:
                file.write(response)

            response_json_file = path_output_dir / f"response_{datetime_now_str}.json"

            with open(response_json_file, 'w') as json_file:
                json.dump(json_data, json_file)

        # For debugging
        if USE_EXISTING_JSON:

            try:

                # Convert Path to string before using json.loads
                with open(PATH_DEFAULT_ABSTRACT_SYSTEM_EXAMPLE_JSON_FILE, 'r') as file:
                    json_data = json.load(file)

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON file: {e}")
                exit(1)

        # Check if the JSON is valid according to the predefined JSON schema
        if not self.abstract_model_json_validator.is_valid_json_data(json_data):
            ValueError("JSON is not valid!")

        abstract_system = AbstractSystem()
        abstract_system.create_from_json_data(json_data)

        return abstract_system
