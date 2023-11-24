# -*- coding: utf-8 -*-

"""
Main Window of the AI Simscape Model Generation tool.

Last modification: 23.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import threading
import locale

from src import prompt_request_factory
from src.gui.percentage_worker import PercentageWorker
from src.gui.main_window_aisimogen_generated import Ui_MainWindow
from config.gobal_constants import LLM_MODEL_OPENAI_GPT

locale.setlocale(locale.LC_ALL, '')


class Ui_MainWindow_Custom(Ui_MainWindow):

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self.pushButton_generate_response.clicked.connect(self.onclick_generate_response)

    def retranslateUi(self, MainWindow):
        super().retranslateUi(MainWindow)

    def onclick_generate_response(self):

        prompt_str = self.plainTextEdit_prompt.toPlainText()

        worker = PercentageWorker()
        worker.percentageChanged.connect(self.progressBar_request_prompt.setValue)
        worker.textChanged.connect(self.label_progress_request_prompt.setText)
        worker.finished.connect(self.update_on_response)

        threading.Thread(
            target=self.generate_response_runner,
            args=(),
            kwargs=dict(prompt=prompt_str, worker=worker),
            daemon=True,
        ).start()

    def generate_response_runner(self, prompt: str, worker: PercentageWorker):

        worker.percentage = 50
        worker.text = "Request sent..."

        response_str = prompt_request_factory.request(prompt, LLM_MODEL_OPENAI_GPT)

        worker.percentage = 100
        worker.text = "Response received!"
        worker.finish(response_str)

    def update_on_response(self, response: str):
        self.plainTextEdit_response.setPlainText(response)
