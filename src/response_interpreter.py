# -*- coding: utf-8 -*-

"""
Response Interpreter

Last modification: 01.02.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import json
from datetime import datetime

from config.gobal_constants import (PATH_DEFAULT_JSON_SCHEMA_FILE, PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE,
                                    PATH_DEFAULT_RESPONSES_DIR)

from src.abstract_model.abstract_system import AbstractSystem
from src.tools.custom_errors import JSONSchemaError
from src.utils.json_schema_validator import JSONSchemaValidator


class ResponseInterpreter:

    def __init__(self):
        self.json_validator = JSONSchemaValidator(PATH_DEFAULT_JSON_SCHEMA_FILE)
        self.abstract_model_json_validator = JSONSchemaValidator(PATH_DEFAULT_ABSTRACT_SYSTEM_JSON_SCHEMA_FILE)

    def interpret_abstract_model_json_response(self, response: str, save_to_disk: bool = True) -> (dict, AbstractSystem):
        """
        Interpret the response of the LLM which is expected to contain the abstract system model in json form.

        :param response: The LLMs response as a string.
        :param save_to_disk: If true, save json object to disk.
        :return: The json object as dictionary and the AbstractSystem object.

        :raises JSONDecodeError: If the string response cannot be decoded as JSON into a dictionary
        :raises JSONSchemaError: If the JSON contained in the response string is invalid
        :raises AbstractComponentError: If there is an error with an abstract component (f.e. wrong name)
        :raises AbstractConnectionError: If there is an error with an abstract connection (f.e. wrong ports)
        """

        # Parse the response as JSON
        json_data = json.loads(response)
        print("JSON object extracted successfully")

        if save_to_disk:

            # Save complete response (debugging)
            datetime_now = datetime.now()
            datetime_now_str = datetime_now.strftime("%Y%m%d_%H%M")

            path_output_dir = PATH_DEFAULT_RESPONSES_DIR / f"api_call_{datetime_now_str}"

            if not path_output_dir.is_dir():
                path_output_dir.mkdir(parents=True)

            response_json_file = path_output_dir / f"response_{datetime_now_str}.json"

            with open(response_json_file, 'w') as json_file:
                json.dump(json_data, json_file)

        # Check if the JSON is valid according to the predefined JSON schema
        if not self.abstract_model_json_validator.is_valid_json_data(json_data):
            raise JSONSchemaError("JSON is not valid!")

        abstract_system = AbstractSystem()
        abstract_system.create_from_json_data(json_data)

        return json_data, abstract_system
