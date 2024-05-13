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

This module creates the PyQT GUI window.

Last modification: 13.05.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load api-keys as environment variables (before other project imports)
load_dotenv(Path(".env"))

import ctypes
from PyQt5 import QtWidgets, QtCore

import src.gui.main_window_aisimogen_custom as MainWindow

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, False)     # enable high-dpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, False)        # use high-dpi icons


def main():

    myappid = u'aisimogen.v1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QtWidgets.QApplication(sys.argv)
    GUI = QtWidgets.QMainWindow()

    ui = MainWindow.Ui_MainWindow_Custom()
    ui.setupUi(GUI)

    GUI.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
