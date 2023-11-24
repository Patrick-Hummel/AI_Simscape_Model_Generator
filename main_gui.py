# -*- coding: utf-8 -*-

"""
This module creates the PyQT GUI window.

Last modification: 23.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load api-keys as environment variables (before other project imports)
load_dotenv(Path(".env"))

from PyQt5 import QtWidgets, QtCore

import src.gui.main_window_aisimogen_custom as MainWindow

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, False)     # enable high-dpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, False)        # use high-dpi icons


def main():

    app = QtWidgets.QApplication(sys.argv)
    GUI = QtWidgets.QMainWindow()

    ui = MainWindow.Ui_MainWindow_Custom()
    ui.setupUi(GUI)

    GUI.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
