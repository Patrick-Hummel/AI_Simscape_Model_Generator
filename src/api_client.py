# -*- coding: utf-8 -*-

"""
Use of the "Singleton" design pattern to only allow single instances of API clients for prompt requests.

Singleton metaclass solution inspired by the answer of user "WorldSEnder" on Stack Overflow (07.07.2015):
https://stackoverflow.com/questions/31269974/why-singleton-in-python-calls-init-multiple-times-and-how-to-avoid-it
Answer: https://stackoverflow.com/a/31270973 User: https://stackoverflow.com/users/3102935/worldsender


Last modification: 23.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from openai import OpenAI


class Singleton(type):
    def __init__(self, name, bases, mmbs):
        super(Singleton, self).__init__(name, bases, mmbs)
        self._instance = super(Singleton, self).__call__()

    def __call__(self, *args, **kw):
        return self._instance


class OpenAIGPTClient(metaclass=Singleton):

    def __init__(self):
        self.client = OpenAI()
        print("Newly created!")

    def request(self, prompt: str) -> str:

        # print(f"Created prompt: {prompt}")

        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        return completion.choices[0].message.content


class GoogleBardClient(metaclass=Singleton):

    def __init__(self):
        pass

    def request(self, prompt: str):
        raise NotImplementedError
