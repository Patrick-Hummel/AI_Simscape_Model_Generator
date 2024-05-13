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

Help Dialog Window

Last modification: 13.05.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog

from src.gui import help_dialog_aisimogen_generated


class HelpDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Set up the user interface from Designer
        self.ui = help_dialog_aisimogen_generated.Ui_HelpDialog()
        self.ui.setupUi(self)

        self.setWindowIcon(QIcon(str(Path(__file__).parent / 'aisimogen_icon_64x64_v2.png')))
