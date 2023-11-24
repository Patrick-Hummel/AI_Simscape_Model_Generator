# AI Simscape Model Generator

By **Patrick Hummel**

Python 3.11 (due to MATLAB R2023B)

Required packages:
* **openai** - The OpenAI Python library provides convenient access to the OpenAI REST API from any Python 3.7+ application.
* **python-dotenv** - Python-dotenv reads key-value pairs from a .env file and can set them as environment variables.
* **matlabengine** - The MATLAB® Engine API for Python® provides a package to integrate MATLAB functionality directly with a Python application, creating an interface to call functions from your MATLAB installation from Python code.
* **jsonschema** - An implementation of the JSON Schema specification for Python.
* **PyQt5** - PyQt5 is a comprehensive set of Python bindings for Qt v5.

**Hint**: To use an API token, create a ".env" file directly in the project directory and include the key "OPENAI_API_KEY=" followed by your token (in this case for OpenAI's LLM API).