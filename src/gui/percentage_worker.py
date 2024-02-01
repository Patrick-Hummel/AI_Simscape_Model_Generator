# -*- coding: utf-8 -*-

"""
Worker that allows updating progress bars and labels using PyQt signals across different threads.

Worker solution inspired by the answer of user "eyllanesc" on Stack Overflow (18.02.2021):
https://stackoverflow.com/questions/66265219/how-to-update-pyqt-progressbar-from-an-independent-function-with-arguments
Answer: https://stackoverflow.com/a/66266068 User: https://stackoverflow.com/users/6622587/eyllanesc

Last modification: 01.02.2024
"""

__version__ = "2"
__author__ = "Patrick Hummel"

from typing import Callable, Union

from PyQt5 import QtCore
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QProgressBar, QLabel


class PercentageWorker(QtCore.QObject):

    started = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal(object)
    percentageChanged = QtCore.pyqtSignal(int)
    textChanged = QtCore.pyqtSignal(str)

    def __init__(self, progress_bar: QProgressBar | None = None,
                 progress_bar_label: QLabel | None = None,
                 on_finished: Union[Callable, None] = None,
                 parent: QObject | None = None):

        super().__init__(parent)
        self._percentage = 0
        self._text = ""

        if progress_bar is not None:
            self.percentageChanged.connect(progress_bar.setValue)

        if progress_bar_label is not None:
            self.textChanged.connect(progress_bar_label.setText)

        if on_finished is not None:
            self.finished.connect(on_finished)

    @property
    def percentage(self):
        return self._percentage

    @percentage.setter
    def percentage(self, value):
        if self._percentage == value:
            return
        self._percentage = value
        self.percentageChanged.emit(self.percentage)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if self._text == value:
            return
        self._text = value
        self.textChanged.emit(self.text)

    def start(self):
        self.started.emit()

    def finish(self, value=None):
        self.finished.emit(value)


class FakeWorker:
    def start(self):
        pass

    def finish(self, value=None):
        pass

    @property
    def percentage(self):
        return 0

    @percentage.setter
    def percentage(self, value):
        pass

    @property
    def text(self):
        return 0

    @text.setter
    def text(self, value):
        pass
