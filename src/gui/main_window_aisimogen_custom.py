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

Main Window of the AI Simscape Model Generation tool.

Last modification: 13.05.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

import copy
import json
import threading
import locale
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import networkx as nx
from PyQt5.QtGui import QIcon
from shapely import LineString
from shapely.geometry import Point

from PyQt5.QtWidgets import QTreeWidgetItem, QGroupBox, QMessageBox, QVBoxLayout, QCheckBox
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5 import QtCore

from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from config.gobal_constants import PATH_EXAMPLE_USER_SPECIFICATION
from src.abstract_model.abstract_components import AbstractComponent

from src.abstract_model.abstract_system import AbstractSystem
from src.api_client import token_cost_calculation
from src.gui.about_dialog_aisimogen_custom import AboutDialog
from src.gui.help_dialog_aisimogen_custom import HelpDialog
from src.language_model_enum import LLModel

from src.gui.percentage_worker import PercentageWorker
from src.gui.main_window_aisimogen_generated import Ui_MainWindow

from src.model.components import ComponentBlock
from src.model.response import ResponseData
from src.model.system import System, Subsystem, Connection
from src.model_upgrader import BasicUpgrader, SingleUpgrader, CombineUpgrader, SINGLE_UPGRADER_COMPARATOR_PATTERN, \
    SINGLE_UPGRADER_VOTER_PATTERN, COMBINED_UPGRADER_C_AND_V_PATTERN, COMBINED_UPGRADER_V_AND_C_PATTERN, \
    COMBINED_UPGRADER_C_AND_S_PATTERN, COMBINED_UPGRADER_V_AND_C_AND_S_PATTERN

from src.prompt_generator import PromptGenerator
from src.response_interpreter import ResponseInterpreter
from src.simscape.interface import Implementer, SystemSimulinkAdapter
from src.system_builder import SystemBuilder

from src.tools.custom_errors import JSONSchemaError, AbstractComponentError, AbstractConnectionError
from src.tools.format_time import seconds_to_string
from src.tools.state_machine import StateMachine, State

locale.setlocale(locale.LC_ALL, '')

PROMPT_HIST_TYPE_PROMPT = "PROMPT"
PROMPT_HIST_TYPE_RESPONSE = "RESPONSE"

DEFAULT_LLM_PROMPT_TEMPERATURE = 1.0

FUNCTION_CALL_CAPABLE_MODELS = [LLModel.OPENAI_GPT35_Turbo, LLModel.MISTRAL_MIXTRAL_8X7B]


class Ui_MainWindow_Custom(Ui_MainWindow):

    def __init__(self):

        self.state_machine = StateMachine(window=self)

        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens_used = 0
        self.total_token_cost_usd = 0.0

        self.abstract_system_model = None
        self.previous_abstract_system_model = None
        self.detailed_system_model = None
        self.previous_detailed_system_model = None

        self.last_response_str = ""
        self.last_json_response_str = ""

        self.current_model = LLModel.OPENAI_GPT35_Turbo
        self.prompt_generator = PromptGenerator(offline_mode=False, temperature=DEFAULT_LLM_PROMPT_TEMPERATURE)

        self.selection_abstract_component_checkbox_dict = {}
        self.selected_abstract_component_types_dict = {}

        self.implemented_abstract_component_types_dict = AbstractComponent.get_implemented_component_types_dict()
        self.implemented_component_block_types_dict = ComponentBlock.get_implemented_component_types_dict()
        self.implemented_default_subsystem_dict = Subsystem.get_implemented_default_subsystems_dict()

        self.fig_abstract = None
        self.ax_abstract = None
        self.canvas_abstract = None
        self.cursor_abstract = None

        self.fig_detailed = None
        self.ax_detailed = None
        self.canvas_detailed = None
        self.cursor_detailed = None

        self.fig_selected_subsystem = None
        self.ax_selected_subsystem = None
        self.canvas_selected_subsystem = None
        self.cursor_selected_subsystem = None

        self.graph_abstract_model = None
        self.pos_abstract_model = {}

        self.graph_detailed_model = None
        self.pos_detailed_model = {}

        self.graph_selected_subsystem = None
        self.pos_selected_subsystem = {}

        self.detailed_system_components_subsystems_list = []
        self.detailed_model_deletion_selection = ""

        self.selected_subsystem_components_list = []

        self.detailed_model_primary_selection = ""
        self.primary_selection_component = None
        self.primary_selection_subsystem = None

        self.current_displayed_subsystem = None

        self.detailed_model_secondary_selection = ""

        self.offline_mode = True

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)

        MainWindow.setWindowIcon(QIcon(str(Path(__file__).parent / 'aisimogen_icon_64x64_v2.png')))

        model_name_list = []
        start_model = self.current_model
        start_model_index = 0

        for idx, model in enumerate(list(LLModel)):
            model_name_list.append(model.name)

            if model is start_model:
                start_model_index = idx

        self.comboBox_current_model.addItems(model_name_list)
        self.comboBox_current_model.setCurrentIndex(start_model_index)
        self.comboBox_add_component.addItems(self.implemented_component_block_types_dict.keys())
        self.comboBox_add_subsystem.addItems(self.implemented_default_subsystem_dict.keys())

        self.comboBox_add_connection_from.currentIndexChanged.connect(self.on_connection_from_changed)
        self.comboBox_add_connection_to.currentIndexChanged.connect(self.on_connection_to_changed)

        self.pushButton_create_specification_summary.clicked.connect(self.on_click_create_specification_summary)
        self.pushButton_verify_specification_summary.clicked.connect(self.on_click_create_abstract_system_model)
        self.pushButton_abstract_model_send_feedback.clicked.connect(self.on_click_send_feedback_on_abstract_model)
        self.pushButton_clear_abstract_model_feedback_text.clicked.connect(self.on_click_clear_abstract_model_feedback)
        self.pushButton_abstract_model_manual_auto_correction.clicked.connect(self.on_click_manual_autocorrection)
        self.pushButton_create_detailed_model.clicked.connect(self.on_click_create_detailed_system_model)

        self.pushButton_detailed_model_add_component.clicked.connect(self.on_click_add_detailed_model_component)
        self.pushButton_detailed_model_add_subsystem.clicked.connect(self.on_click_add_detailed_model_subsystem)
        self.pushButton_detailed_model_add_connection.clicked.connect(self.on_click_add_detailed_model_connection)
        self.pushButton_detailed_model_delete_selection.clicked.connect(self.on_click_delete_selection_from_detailed_model)
        self.pushButton_detailed_model_update_parameters.clicked.connect(self.update_component_parameters)
        self.pushButton_single_upgrader.clicked.connect(self.on_click_single_upgrade_detailed_model)
        self.pushButton_combined_upgrader.clicked.connect(self.on_click_combined_upgrade_detailed_model)
        self.pushButton_build_simscape_model.clicked.connect(self.on_click_build_simscape_model)

        self.action_undo_change_to_abstract_model.triggered.connect(self.on_action_undo_abstract_model)
        self.action_undo_change_to_detailed_model.triggered.connect(self.on_action_undo_detailed_model)
        self.action_save_to_file_abstract.triggered.connect(self.on_action_save_to_file_abstract_model)
        self.action_save_to_file_detailed.triggered.connect(self.on_action_save_to_file_detailed_model)

        self.action_undo_change_to_abstract_model.setEnabled(False)
        self.action_undo_change_to_detailed_model.setEnabled(False)
        self.action_about.triggered.connect(self.show_about_dialog)
        self.action_how_to_use.triggered.connect(self.show_help_dialog)

        self.comboBox_single_upgrader_pattern.addItems([SINGLE_UPGRADER_COMPARATOR_PATTERN, SINGLE_UPGRADER_VOTER_PATTERN])
        self.comboBox_combined_upgrader_pattern.addItems([COMBINED_UPGRADER_C_AND_V_PATTERN,
                                                          COMBINED_UPGRADER_V_AND_C_PATTERN,
                                                          COMBINED_UPGRADER_C_AND_S_PATTERN,
                                                          COMBINED_UPGRADER_V_AND_C_AND_S_PATTERN])

        with open(PATH_EXAMPLE_USER_SPECIFICATION, 'r') as file:
            example_user_specification_str = file.read()

        self.plainTextEdit_user_specification.setPlainText(example_user_specification_str)

        self.doubleSpinBox_config_model_temperature.setValue(DEFAULT_LLM_PROMPT_TEMPERATURE)
        self.doubleSpinBox_config_model_temperature.valueChanged.connect(self.on_value_changed_temperature_spinbox)

        # Create matplotlib plot within groupbox
        self.fig_abstract, self.ax_abstract, self.canvas_abstract = _create_matplotlib_figure_groupbox(
            self.groupBox_abstract_model_visualization)

        # Connect the Matplotlib cursor event
        # self.cursor_abstract = self.canvas_abstract.mpl_connect('button_press_event', self.on_canvas_abstract_click)

        # Create matplotlib plot within groupbox
        self.fig_detailed, self.ax_detailed, self.canvas_detailed = _create_matplotlib_figure_groupbox(
            self.groupBox_detailed_model_visualization)

        # Connect the Matplotlib cursor event
        self.cursor_detailed = self.canvas_detailed.mpl_connect('button_press_event', self.on_canvas_detailed_model_click)#

        # Create matplotlib plot within groupbox
        self.fig_selected_subsystem, self.ax_selected_subsystem, self.canvas_selected_subsystem = _create_matplotlib_figure_groupbox(
            self.groupBox_detailed_model_subsystem_visualization)

        # Connect the Matplotlib cursor event
        self.cursor_selected_subsystem = self.canvas_selected_subsystem.mpl_connect('button_press_event', self.on_canvas_selected_subsystem_click)

        # Temporary for debugging
        self.label_info_current_state.setText(self.state_machine.current_state.name)

        self.tabWidget_main.tabBar().setTabEnabled(1, False)
        self.tabWidget_main.tabBar().setTabEnabled(2, False)

        # --- Build abstract component selection dynamically ---
        # Create a widget to contain the checkboxes
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Add checkboxes to the layout
        for component_type in list(self.implemented_abstract_component_types_dict.keys()):
            checkbox = QCheckBox(component_type)
            checkbox.setChecked(True)
            scroll_layout.addWidget(checkbox)
            self.selection_abstract_component_checkbox_dict[component_type] = checkbox

        # Set the layout of the scroll content
        scroll_content.setLayout(scroll_layout)

        # Set the scroll area widget
        self.scrollArea_abstract_components_selection.setWidget(scroll_content)

        self.detailed_model_param_labels_list = [self.label_desc_detailed_model_param_1,
                                                 self.label_desc_detailed_model_param_2,
                                                 self.label_desc_detailed_model_param_3,
                                                 self.label_desc_detailed_model_param_4,
                                                 self.label_desc_detailed_model_param_5,
                                                 self.label_desc_detailed_model_param_6,
                                                 self.label_desc_detailed_model_param_7,
                                                 self.label_desc_detailed_model_param_8,
                                                 self.label_desc_detailed_model_param_9]

        self.detailed_model_param_line_edits_list = [self.lineEdit_detailed_model_param_1,
                                                 self.lineEdit_detailed_model_param_2,
                                                 self.lineEdit_detailed_model_param_3,
                                                 self.lineEdit_detailed_model_param_4,
                                                 self.lineEdit_detailed_model_param_5,
                                                 self.lineEdit_detailed_model_param_6,
                                                 self.lineEdit_detailed_model_param_7,
                                                 self.lineEdit_detailed_model_param_8,
                                                 self.lineEdit_detailed_model_param_9]

    def retranslateUi(self, MainWindow):
        super().retranslateUi(MainWindow)

    def on_value_changed_temperature_spinbox(self):
        self.prompt_generator.temperature = self.doubleSpinBox_config_model_temperature.value()
        print(f"Temperature set to: {self.prompt_generator.temperature}")

    def update_selected_abstract_component_type(self):

        self.selected_abstract_component_types_dict = {}

        for checkbox in self.selection_abstract_component_checkbox_dict.keys():

            if self.selection_abstract_component_checkbox_dict[checkbox].isChecked():
                self.selected_abstract_component_types_dict[checkbox] = self.implemented_abstract_component_types_dict[checkbox]

            else:
                print(f"Not selected: {checkbox}")

        self.prompt_generator.create_system_modeling_instructions(self.selected_abstract_component_types_dict)

    def show_error_dialog(self, title: str, text: str, informative_text: str) -> bool:

        # Create and show the error dialog
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle(title)
        error_dialog.setWindowIcon(QIcon(str(Path(__file__).parent / 'aisimogen_icon_64x64_v2.png')))
        error_dialog.setText(text)
        error_dialog.setInformativeText(informative_text)
        error_dialog.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
        response = error_dialog.exec_()

        if response == QMessageBox.Retry:
            return True
        elif response == QMessageBox.Cancel:
            return False
        else:
            return False

    def show_success_dialog(self, title: str, text: str, informative_text: str) -> bool:

        # Create and show the error dialog
        success_dialog = QMessageBox()
        success_dialog.setIcon(QMessageBox.Information)
        success_dialog.setWindowTitle(title)
        success_dialog.setWindowIcon(QIcon(str(Path(__file__).parent / 'aisimogen_icon_64x64_v2.png')))
        success_dialog.setText(text)
        success_dialog.setInformativeText(informative_text)
        success_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        response = success_dialog.exec_()

        if response == QMessageBox.Yes:
            return True
        elif response == QMessageBox.No:
            return False
        else:
            return False

    def show_about_dialog(self):
        about_dialog = AboutDialog()
        about_dialog.exec_()

    def show_help_dialog(self):
        about_dialog = HelpDialog()
        about_dialog.exec_()

    def _update_gui_on_prompt_response(self, prompt: str, response: ResponseData, prompt_title: str, response_title: str):

        self._update_prompt_history(PROMPT_HIST_TYPE_PROMPT, prompt_title, prompt)
        self._update_prompt_history(PROMPT_HIST_TYPE_RESPONSE, response_title, response.response_str)

        self.label_last_response_time.setText(seconds_to_string(response.time_seconds))

        # Calculate total token count of response and add it to overall total of generation process
        self.total_tokens_used += (response.input_tokens + response.output_tokens)
        self.label_total_tokens.setText(f"{self.total_tokens_used}")

        # Calculate total token cost of response and add it to overall cost of generation process
        input_cost, output_cost = token_cost_calculation(input_tokens=response.input_tokens,
                                                         output_tokens=response.output_tokens,
                                                         model_name=response.model_name)

        self.total_token_cost_usd += (input_cost + output_cost)
        self.label_total_cost_euro.setText(f"{self.total_token_cost_usd:.5f}")

    def _update_prompt_history(self, msg_type: str, title: str, text: str):

        # Include current date in filename
        datetime_now = datetime.now()
        datetime_now_str = datetime_now.strftime("%d.%m.%Y - %H:%M:%S")

        self.plainTextEdit_prompt_history.appendPlainText(f"----- {msg_type} ({title}) - {self.current_model.name} - {datetime_now_str} -----\n{text}\n")

    def on_action_undo_abstract_model(self):
        self.abstract_system_model = self.previous_abstract_system_model
        self.action_undo_change_to_abstract_model.setEnabled(False)
        self.on_update_abstract_system_model_created()

    def on_action_undo_detailed_model(self):
        self.detailed_system_model = self.previous_detailed_system_model
        self.action_undo_change_to_detailed_model.setEnabled(False)
        self.on_update_detailed_system_model_created()

    def on_action_save_to_file_abstract_model(self):
        raise NotImplementedError("Save to file not yet implemented for abstract model.")

    def on_action_save_to_file_detailed_model(self):
        if self.detailed_system_model is not None and len(self.detailed_system_model) > 0:
            self.detailed_system_model.save_as_json()
            print("Detailed model was saved as JSON.")
        else:
            print("You need to generate a detailed system model before you can save it to disk.")

    def on_click_add_detailed_model_component(self):

        if self.detailed_system_model is not None:

            self.previous_detailed_system_model = copy.deepcopy(self.detailed_system_model)
            self.action_undo_change_to_detailed_model.setEnabled(True)

            new_component_type = self.implemented_component_block_types_dict[self.comboBox_add_component.currentText()]
            self.detailed_system_model.add_component(new_component_type())
            self.on_update_detailed_system_model_created()

    def on_click_add_detailed_model_subsystem(self):

        if self.detailed_system_model is not None:

            self.previous_detailed_system_model = copy.deepcopy(self.detailed_system_model)
            self.action_undo_change_to_detailed_model.setEnabled(True)

            new_default_subsystem_type = self.implemented_default_subsystem_dict[self.comboBox_add_subsystem.currentText()]
            self.detailed_system_model.add_subsystem(new_default_subsystem_type())
            self.on_update_detailed_system_model_created()

    def on_click_add_detailed_model_connection(self):

        if self.detailed_system_model is not None:

            self.previous_detailed_system_model = copy.deepcopy(self.detailed_system_model)
            self.action_undo_change_to_detailed_model.setEnabled(True)

            from_block_selection_str = self.comboBox_add_connection_from.currentText()
            to_block_selection_str = self.comboBox_add_connection_to.currentText()

            from_block_selection = None
            to_block_selection = None

            for comp in self.detailed_system_model.component_list:
                if comp.unique_name == from_block_selection_str:
                    from_block_selection = comp
                    from_port_selection = comp.ports[0]
                if comp.unique_name == to_block_selection_str:
                    to_block_selection = comp
                    to_port_selection = comp.ports[0]

            for subsys in self.detailed_system_model.subsystem_list:
                if subsys.unique_name == from_block_selection_str:
                    from_block_selection = subsys
                    from_port_selection = subsys.out_ports[0].unique_name
                if subsys.unique_name == to_block_selection_str:
                    to_block_selection = subsys
                    to_port_selection = subsys.in_ports[0].unique_name

            # from_port_selection = self.comboBox_add_connection_from_port.currentText()
            # to_port_selection = self.comboBox_add_connection_to_port.currentText()

            if from_block_selection is not None or to_block_selection is not None:

                new_connection = Connection(from_block=from_block_selection, from_port=from_port_selection,
                                            to_block=to_block_selection, to_port=to_port_selection)

                self.detailed_system_model.add_connection(new_connection)
                self.on_update_detailed_system_model_created()

    def on_click_delete_selection_from_detailed_model(self):

        if self.detailed_system_model is not None:

            # TODO find a better way than to differentiate by value type
            # A node was selected if it is a string
            if isinstance(self.detailed_model_deletion_selection, str):

                if self.detailed_model_deletion_selection in self.detailed_system_model.list_components():
                    self.detailed_system_model.remove_component_by_unique_name(self.detailed_model_deletion_selection)
                    self.on_update_detailed_system_model_created()
                    return
                elif self.detailed_model_deletion_selection in self.detailed_system_model.list_subsystems():
                    self.detailed_system_model.remove_subsystem_by_unique_name(self.detailed_model_deletion_selection)
                    self.on_update_detailed_system_model_created()
                    return

            if isinstance(self.detailed_model_deletion_selection, tuple):
                from_component_unique_name = self.detailed_model_deletion_selection[0]
                to_component_unique_name = self.detailed_model_deletion_selection[1]
                self.detailed_system_model.remove_connection_by_component_names(from_component_unique_name, to_component_unique_name)
                self.on_update_detailed_system_model_created()
                return

    def on_click_create_specification_summary(self):

        # Communicate progress across different threads using a worker
        worker = PercentageWorker(progress_bar=self.progressBar_main_request,
                                  progress_bar_label=self.label_progress_main_request,
                                  on_finished=self.update_on_specification_summary_creation)

        # Run in other thread
        run_thread(self.create_specification_summary_runner, worker)

    def create_specification_summary_runner(self, worker: PercentageWorker):

        usr_str = self.plainTextEdit_user_specification.toPlainText()

        worker.percentage = 50
        worker.text = "Waiting for response..."

        self.current_model = LLModel.from_str(name=self.comboBox_current_model.currentText())

        prompt, response = self.prompt_generator.generate_prompt_create_specification_summary(usr_str, llm_model=self.current_model)

        self._update_gui_on_prompt_response(prompt=prompt, response=response,
                                            prompt_title="Create specification summary",
                                            response_title="Specification summary")

        worker.percentage = 100
        worker.text = "Summary received."
        worker.finish(response.response_str)

    def update_on_specification_summary_creation(self, response: str):
        self.plainTextEdit_specification_summary.setPlainText(response)

        # State machine transition
        self.state_machine.set_state(State.SPECIFICATION_SUMMARIZED)

    def interpret_abstract_model_json_response(self, worker: PercentageWorker):

        worker.percentage = 66
        worker.text = "Interpreting response..."

        # 3) Interpret response
        response_interpreter = ResponseInterpreter()

        success = False
        counter = 0
        MAX_LOOP_COUNT = 3

        while (not success) and (counter < MAX_LOOP_COUNT):

            try:

                json_data, temp_abstract_system_model = response_interpreter.interpret_abstract_model_json_response(self.last_response_str)

                # If interpretation successful, update models (and set previous model for undo functionality)
                self.previous_abstract_system_model = copy.deepcopy(self.abstract_system_model)
                self.abstract_system_model = temp_abstract_system_model
                self.action_undo_change_to_abstract_model.setEnabled(True)

                self.treeWidget_json_response.clear()
                add_items_to_tree_json_response(self.treeWidget_json_response.invisibleRootItem(), json_data)

                self.treeWidget_abstract_model.clear()
                add_items_to_tree_abstract_system_model(self.treeWidget_abstract_model.invisibleRootItem(),
                                                        self.abstract_system_model)

                success = True

            except json.JSONDecodeError as jde:
                print(f"Error decoding JSON: {jde}")

                worker.percentage = 90
                worker.text = "Error decoding JSON"
                return

            except JSONSchemaError as jse:
                print(f"Error interpreting response: {jse}")

                worker.percentage = 90
                worker.text = "JSON schema invalid"
                return

            except AbstractComponentError as acompe:
                print(f"Error interpreting response: {acompe} {acompe.list_wrong_components}")

                worker.percentage = 90
                worker.text = f"Component autocorrect... Retry ({counter + 1})"

                use_function_call = self.checkBox_config_function_call_prompt.isChecked()

                prompt, response = self.prompt_generator.generate_prompt_autocorrect_abstract_model(
                    abstract_system_model_json=self.last_response_str, error=acompe,
                    llm_model=self.current_model, function_call_prompt=use_function_call)

                self._update_gui_on_prompt_response(prompt=prompt, response=response,
                                                    prompt_title="Auto correct for abstract system model",
                                                    response_title="Modified abstract system model")

                self.last_response_str = response.response_str

                counter += 1

            except AbstractConnectionError as acone:
                print(f"Error interpreting response: {acone}")

                worker.percentage = 90
                worker.text = f"Connection autocorrect... Retry ({counter + 1})"

                use_function_call = self.checkBox_config_function_call_prompt.isChecked()

                prompt, response = self.prompt_generator.generate_prompt_autocorrect_abstract_model(
                    abstract_system_model_json=self.last_response_str, error=acone,
                    llm_model=self.current_model, function_call_prompt=use_function_call)

                self._update_gui_on_prompt_response(prompt=prompt, response=response,
                                                    prompt_title="Auto correct for abstract system model",
                                                    response_title="Modified abstract system model")

                self.last_response_str = response.response_str

                counter += 1

        if success:
            worker.percentage = 100
            worker.text = "Abstract system model created."
        else:
            worker.percentage = 0
            worker.text = "Interpretation error..."

        worker.finish(success)

    def on_click_create_abstract_system_model(self):

        # Communicate progress across different threads using a worker
        worker = PercentageWorker(progress_bar=self.progressBar_main_request,
                                  progress_bar_label=self.label_progress_main_request,
                                  on_finished=self.on_update_abstract_system_model_created)

        # Run in other thread
        run_thread(self.create_abstract_system_model_runner, worker)

    def create_abstract_system_model_runner(self, worker: PercentageWorker):

        # Update selected abstract components first
        self.update_selected_abstract_component_type()

        specification_summary_str = self.plainTextEdit_specification_summary.toPlainText()
        self.current_model = LLModel.from_str(name=self.comboBox_current_model.currentText())
        use_function_call = self.checkBox_config_function_call_prompt.isChecked()

        worker.percentage = 50
        worker.text = "Waiting for response..."
        print("Sending new request...")

        # 1) Generate prompt
        prompt, response = self.prompt_generator.generate_prompt_create_abstract_model(system_description=specification_summary_str,
                                                                                       llm_model=self.current_model,
                                                                                       function_call_prompt=use_function_call)

        self._update_gui_on_prompt_response(prompt=prompt, response=response,
                                            prompt_title="Create abstract system model",
                                            response_title="Abstract system model")

        self.last_response_str = response.response_str

        self.interpret_abstract_model_json_response(worker)

    def on_update_abstract_system_model_created(self, success: bool):

        if not success:
            self.state_machine.set_state(State.INTERPRETATION_ERROR)
            return

        self.create_abstract_system_network_graph_plot()
        self.plainTextEdit_ai_abstract_system_model.setPlainText(self.last_response_str)

        # Expand only the first level
        for i in range(self.treeWidget_json_response.topLevelItemCount()):
            item = self.treeWidget_json_response.topLevelItem(i)
            item.setExpanded(True)

        # Expand only the first level
        for i in range(self.treeWidget_abstract_model.topLevelItemCount()):
            item = self.treeWidget_abstract_model.topLevelItem(i)
            item.setExpanded(True)

        self.tabWidget_main.setCurrentIndex(1)

        # State machine transition
        self.state_machine.set_state(State.ABSTRACT_SYSTEM_MODEL_GENERATED)

    def on_click_manual_autocorrection(self):

        # Communicate progress across different threads using a worker
        worker = PercentageWorker(progress_bar=self.progressBar_main_request,
                                  progress_bar_label=self.label_progress_main_request,
                                  on_finished=self.on_update_abstract_system_model_created)

        # Run in other thread
        run_thread(self.request_manual_autocorrection_abstract_model, worker)

    def request_manual_autocorrection_abstract_model(self, worker: PercentageWorker):

        worker.percentage = 50
        worker.text = "Waiting for response..."

        self.current_model = LLModel.from_str(name=self.comboBox_current_model.currentText())
        use_function_call = self.checkBox_config_function_call_prompt.isChecked()

        prompt, response = self.prompt_generator.generate_prompt_autocorrect_abstract_model(
            self.last_response_str, error=None,
            llm_model=self.current_model, function_call_prompt=use_function_call)

        self._update_gui_on_prompt_response(prompt=prompt, response=response,
                                            prompt_title="Manual autocorrect request for abstract system model",
                                            response_title="Modified abstract system model")

        self.last_response_str = response.response_str

        self.interpret_abstract_model_json_response(worker)

    def on_click_send_feedback_on_abstract_model(self):

        # Communicate progress across different threads using a worker
        worker = PercentageWorker(progress_bar=self.progressBar_main_request,
                                  progress_bar_label=self.label_progress_main_request,
                                  on_finished=self.on_update_abstract_system_model_created)

        # Run in other thread
        run_thread(self.send_feedback_on_abstract_model_runner, worker)

    def send_feedback_on_abstract_model_runner(self, worker: PercentageWorker):

        feedback_str = self.plainTextEdit_abstract_model_feedback.toPlainText()
        self.current_model = LLModel.from_str(name=self.comboBox_current_model.currentText())
        use_function_call = self.checkBox_config_function_call_prompt.isChecked()

        worker.percentage = 50
        worker.text = "Waiting for response..."

        prompt, response = self.prompt_generator.generate_prompt_improve_abstract_model_by_feedback(abstract_system_model_json=self.last_response_str,
                                                                                                    feedback=feedback_str,
                                                                                                    llm_model=self.current_model,
                                                                                                    function_call_prompt=use_function_call)

        self._update_gui_on_prompt_response(prompt=prompt, response=response,
                                            prompt_title="Feedback for abstract system model",
                                            response_title="Modified abstract system model")

        self.last_response_str = response.response_str

        self.interpret_abstract_model_json_response(worker)

    def on_click_clear_abstract_model_feedback(self):
        self.plainTextEdit_abstract_model_feedback.clear()

    def on_click_create_detailed_system_model(self):

        # Communicate progress across different threads using a worker
        worker = PercentageWorker(progress_bar=self.progressBar_main_request,
                                  progress_bar_label=self.label_progress_main_request,
                                  on_finished=self.on_update_detailed_system_model_created)

        # Run in other thread
        run_thread(self.create_detailed_system_model_runner, worker)

    def create_detailed_system_model_runner(self, worker: PercentageWorker):

        # 4) Build detailed system
        builder = SystemBuilder(self.abstract_system_model)
        self.previous_detailed_system_model = copy.deepcopy(self.detailed_system_model)
        self.detailed_system_model = builder.build("AISiMoGen")

        worker.percentage = 100
        worker.text = "Created detailed model."
        worker.finish()

    def on_connection_from_changed(self):

        from_block_selection_str = self.comboBox_add_connection_from.currentText()

        for comp in self.detailed_system_model.component_list:
            if comp.unique_name == from_block_selection_str:
                self.comboBox_add_connection_from_port.clear()
                self.comboBox_add_connection_from_port.addItems(comp.ports)

        for subsys in self.detailed_system_model.subsystem_list:
            if subsys.unique_name == from_block_selection_str:
                self.comboBox_add_connection_from_port.clear()

                in_port_list = []
                out_port_list = []

                for in_port in subsys.in_ports:
                    in_port_list.extend(in_port.ports)

                for out_port in subsys.out_ports:
                    out_port_list.extend(out_port.ports)

                self.comboBox_add_connection_from_port.addItems(in_port_list)
                self.comboBox_add_connection_from_port.addItems(out_port_list)

    def on_connection_to_changed(self):

        to_block_selection_str = self.comboBox_add_connection_to.currentText()

        for comp in self.detailed_system_model.component_list:
            if comp.unique_name == to_block_selection_str:
                self.comboBox_add_connection_to_port.clear()
                self.comboBox_add_connection_to_port.addItems(comp.ports)

        for subsys in self.detailed_system_model.subsystem_list:
            if subsys.unique_name == to_block_selection_str:

                in_port_list = []
                out_port_list = []

                for in_port in subsys.in_ports:
                    in_port_list.extend(in_port.ports)

                for out_port in subsys.out_ports:
                    out_port_list.extend(out_port.ports)

                self.comboBox_add_connection_to_port.clear()
                self.comboBox_add_connection_to_port.addItems(in_port_list)
                self.comboBox_add_connection_to_port.addItems(out_port_list)

    def on_update_detailed_system_model_created(self):

        self.detailed_system_components_subsystems_list = []

        for comp in self.detailed_system_model.component_list:
            self.detailed_system_components_subsystems_list.append(comp.unique_name)

        for subsys in self.detailed_system_model.subsystem_list:
            self.detailed_system_components_subsystems_list.append(subsys.unique_name)

        self.comboBox_add_connection_from.clear()
        self.comboBox_add_connection_from.addItems(self.detailed_system_components_subsystems_list)

        self.comboBox_add_connection_to.clear()
        self.comboBox_add_connection_to.addItems(self.detailed_system_components_subsystems_list)

        self.on_connection_from_changed()
        self.on_connection_to_changed()

        self.create_detailed_model_network_graph_plot()

        self.treeWidget_detailed_model.clear()
        add_items_to_tree_detailed_system_model(self.treeWidget_detailed_model.invisibleRootItem(), self.detailed_system_model)

        # Expand only the first level
        for i in range(self.treeWidget_detailed_model.topLevelItemCount()):
            item = self.treeWidget_detailed_model.topLevelItem(i)
            item.setExpanded(True)

        if (len(self.detailed_system_model.subsystem_list) > 0) and (self.primary_selection_subsystem is None):
            subsys = self.detailed_system_model.subsystem_list[0]
            self.detailed_model_primary_selection = subsys.unique_name
            self.primary_selection_subsystem = subsys
            self.current_displayed_subsystem = subsys
            self.create_selected_subsystem_network_graph_plot()
            self.label_detailed_model_upgrade_selected_subsystem.setText(self.detailed_model_primary_selection)

        self.tabWidget_main.setCurrentIndex(2)

        # State machine transition
        self.state_machine.set_state(State.DETAILED_SYSTEM_MODEL_GENERATED)

    def on_update_simscape_model_created(self):

        # State machine transition
        self.state_machine.set_state(State.SIMSCAPE_MODEL_GENERATED)

    def on_click_single_upgrade_detailed_model(self):

        selected_upgrade_pattern = self.comboBox_single_upgrader_pattern.currentText()
        selected_upgrade_target = int(self.spinBox_upgrader_target.value())

        up = BasicUpgrader(self.detailed_system_model)
        sigup = SingleUpgrader(up)

        if self.radioButton_upgrade_all_subsystems.isChecked():

            for subsys in self.detailed_system_model.subsystem_list:

                sigup.upgrade(pattern_name=selected_upgrade_pattern,
                              subsystem_unique_name=subsys.unique_name,
                              target=selected_upgrade_target)

        elif self.radioButton_upgrade_selected_subsystem.isChecked():
            sigup.upgrade(pattern_name=selected_upgrade_pattern,
                          subsystem_unique_name=self.current_displayed_subsystem.unique_name,
                          target=selected_upgrade_target)

        self.selected_subsystem_components_list = []

        for comp in self.current_displayed_subsystem.component_list:
            self.selected_subsystem_components_list.append(comp.unique_name)

        self.on_update_detailed_system_model_created()
        self.create_selected_subsystem_network_graph_plot()

    def on_click_combined_upgrade_detailed_model(self):

        selected_upgrade_pattern = self.comboBox_combined_upgrader_pattern.currentText()
        selected_upgrade_target = int(self.spinBox_upgrader_target.value())

        up = BasicUpgrader(self.detailed_system_model)
        comup = CombineUpgrader(up)

        if self.radioButton_upgrade_all_subsystems.isChecked():

            for subsys in self.detailed_system_model.subsystem_list:
                comup.upgrade(pattern_name=selected_upgrade_pattern,
                              subsystem_unique_name=subsys.unique_name,
                              target=selected_upgrade_target)

        elif self.radioButton_upgrade_selected_subsystem.isChecked():
            comup.upgrade(pattern_name=selected_upgrade_pattern,
                          subsystem_unique_name=self.current_displayed_subsystem.unique_name,
                          target=selected_upgrade_target)

        self.selected_subsystem_components_list = []

        for comp in self.current_displayed_subsystem.component_list:
            self.selected_subsystem_components_list.append(comp.unique_name)

        self.on_update_detailed_system_model_created()
        self.create_selected_subsystem_network_graph_plot()

    def on_click_build_simscape_model(self):

        # Communicate progress across different threads using a worker
        worker = PercentageWorker(progress_bar=self.progressBar_main_request,
                                  progress_bar_label=self.label_progress_main_request,
                                  on_finished=self.on_update_simscape_model_created)

        # Run in other thread
        run_thread(self.build_simscape_model_runner, worker)

    def build_simscape_model_runner(self, worker: PercentageWorker):

        # 5) Create simulink model and save result to disk
        simulink_implementer = Implementer(SystemSimulinkAdapter)
        simulink_implementer.input_to_simulink(self.detailed_system_model, self.detailed_system_model.name, self.pos_detailed_model)
        simulink_implementer.save_to_disk(self.detailed_system_model.name)

        time.sleep(30)

        worker.percentage = 100
        worker.text = "Done."
        worker.finish()

    def create_abstract_system_network_graph_plot(self):

        if self.abstract_system_model is None:
            return

        self.graph_abstract_model = self.abstract_system_model.as_networkx_graph()

        # Clear plot first
        self.ax_abstract.cla()

        # Position nodes (different layouts possible)
        self.pos_abstract_model = nx.spring_layout(self.graph_abstract_model)

        # Plot the graph on the subplot
        nx.draw(self.graph_abstract_model, self.pos_abstract_model, with_labels=True, font_weight='bold', font_size=10,
                ax=self.ax_abstract, node_color='LightGreen')  # node_size=700

        # self.ax_node_profile.autoscale()
        self.fig_abstract.tight_layout()

        self.canvas_abstract.draw()

    def create_detailed_model_network_graph_plot(self, keep_previous_pos: bool = False):

        # Clear plot first
        self.ax_detailed.cla()

        # Create networkx graph
        self.graph_detailed_model = self.detailed_system_model.as_networkx_graph()

        # Check if connected
        if nx.is_connected(self.graph_detailed_model):
            self.label_not_connected_warning.setVisible(False)
        else:
            self.label_not_connected_warning.setVisible(True)

        if not keep_previous_pos or len(self.pos_detailed_model) <= 0:

            # Position nodes (different layouts possible)
            self.pos_detailed_model = nx.spring_layout(self.graph_detailed_model)

        color_map = []

        for n in self.graph_detailed_model.nodes():
            if n == self.detailed_model_deletion_selection:
                color_map.append('red')
            elif n == self.detailed_model_primary_selection:
                color_map.append('orange')
            elif n == self.detailed_model_secondary_selection:
                color_map.append('green')
            else:
                color_map.append('skyblue')

        # Plot the graph on the subplot
        nx.draw(self.graph_detailed_model, self.pos_detailed_model, with_labels=True, font_weight='bold', font_size=10,
                ax=self.ax_detailed, node_color=color_map)  # node_size=700, node_color='skyblue'

        # self.ax_node_profile.autoscale()
        self.fig_detailed.tight_layout()

        self.canvas_detailed.draw()

    def create_selected_subsystem_network_graph_plot(self, keep_previous_pos: bool = False):

        # Clear plot first
        self.ax_selected_subsystem.cla()

        # Create networkx graph
        self.graph_selected_subsystem = self.current_displayed_subsystem.as_networkx_graph()

        if not keep_previous_pos or len(self.pos_selected_subsystem) <= 0:

            # Position nodes (different layouts possible)
            self.pos_selected_subsystem = nx.spring_layout(self.graph_selected_subsystem)

        color_map = []

        for n in self.graph_selected_subsystem.nodes():
            if n == self.detailed_model_deletion_selection:
                color_map.append('red')
            elif n == self.detailed_model_primary_selection:
                color_map.append('orange')
            elif n == self.detailed_model_secondary_selection:
                color_map.append('green')
            else:
                color_map.append('skyblue')

        # Plot the graph on the subplot
        nx.draw(self.graph_selected_subsystem, self.pos_selected_subsystem, with_labels=True, font_weight='bold', font_size=10,
                ax=self.ax_selected_subsystem, node_color=color_map)  # node_size=700, node_color='skyblue'

        # self.ax_node_profile.autoscale()
        self.fig_selected_subsystem.tight_layout()

        self.canvas_selected_subsystem.draw()

    def on_canvas_selected_subsystem_click(self, event):

        if event.inaxes == self.ax_selected_subsystem:
            x, y = event.xdata, event.ydata

            # Check if a node is clicked
            node_clicked = self.pick_node(x, y, self.graph_selected_subsystem, self.pos_selected_subsystem)

            if node_clicked is not None:

                node_clicked_index = self.selected_subsystem_components_list.index(node_clicked)

                # Left button: 1, Middle button (Scroll wheel): 2, Right button: 3
                if event.button == 1:
                    self.detailed_model_primary_selection = node_clicked
                    self.comboBox_add_connection_from.setCurrentIndex(node_clicked_index)
                    self.interpret_primary_click_selected_subsystem()

                elif event.button == 2:
                    self.detailed_model_deletion_selection = node_clicked
                    self.label_detailed_model_deletion_selection.setText(node_clicked)
                    self.create_selected_subsystem_network_graph_plot(keep_previous_pos=True)

                elif event.button == 3:
                    self.detailed_model_secondary_selection = node_clicked
                    self.comboBox_add_connection_to.setCurrentIndex(node_clicked_index)
                    self.create_selected_subsystem_network_graph_plot(keep_previous_pos=True)

            else:
                # Check if an edge is clicked only if a node was not selected (nodes have priority)
                edge_clicked = self.pick_edge(x, y, self.graph_selected_subsystem, self.pos_selected_subsystem)

                if edge_clicked is not None:
                    if event.button == 2:
                        self.detailed_model_deletion_selection = edge_clicked
                        self.label_detailed_model_deletion_selection.setText(f"{edge_clicked[0]} -> {edge_clicked[1]}")

    def on_canvas_detailed_model_click(self, event):

        if event.inaxes == self.ax_detailed:
            x, y = event.xdata, event.ydata

            # Check if a node is clicked
            node_clicked = self.pick_node(x, y, self.graph_detailed_model, self.pos_detailed_model)

            if node_clicked is not None:

                node_clicked_index = self.detailed_system_components_subsystems_list.index(node_clicked)

                # Left button: 1, Middle button (Scroll wheel): 2, Right button: 3
                if event.button == 1:
                    self.detailed_model_primary_selection = node_clicked
                    self.comboBox_add_connection_from.setCurrentIndex(node_clicked_index)
                    self.interpret_primary_click()

                elif event.button == 2:
                    self.detailed_model_deletion_selection = node_clicked
                    self.label_detailed_model_deletion_selection.setText(node_clicked)
                    self.create_detailed_model_network_graph_plot(keep_previous_pos=True)

                elif event.button == 3:
                    self.detailed_model_secondary_selection = node_clicked
                    self.comboBox_add_connection_to.setCurrentIndex(node_clicked_index)
                    self.create_detailed_model_network_graph_plot(keep_previous_pos=True)

            else:
                # Check if an edge is clicked only if a node was not selected (nodes have priority)
                edge_clicked = self.pick_edge(x, y, self.graph_detailed_model, self.pos_detailed_model)

                if edge_clicked is not None:
                    if event.button == 2:
                        self.detailed_model_deletion_selection = edge_clicked
                        self.label_detailed_model_deletion_selection.setText(f"{edge_clicked[0]} -> {edge_clicked[1]}")

    @staticmethod
    def pick_node(x, y, graph, pos):

        for node in graph.nodes():
            click_point = Point(x, y)
            node_x, node_y = pos[node]
            node_center_point = Point(node_x, node_y)
            if click_point.distance(node_center_point) < 0.05:  # Adjust this threshold as needed
                return node
        return None

    @staticmethod
    def pick_edge(x, y, graph, pos):

        for edge in graph.edges():

            node1, node2 = edge

            node1_x, node1_y = pos[node1]
            node2_x, node2_y = pos[node2]

            click_point = Point(x, y)
            edge_line = LineString([(node1_x, node1_y), (node2_x, node2_y)])

            if click_point.distance(edge_line) < 0.05:  # Adjust this threshold as needed
                return node1, node2

        return None

    def interpret_primary_click(self):

        self.primary_selection_component = None
        self.primary_selection_subsystem = None

        for subsys in self.detailed_system_model.subsystem_list:

            if self.detailed_model_primary_selection == subsys.unique_name:

                self.primary_selection_subsystem = subsys
                self.current_displayed_subsystem = subsys

                self.create_selected_subsystem_network_graph_plot()
                self.label_detailed_model_upgrade_selected_subsystem.setText(self.detailed_model_primary_selection)

                self.selected_subsystem_components_list = []

                for comp in subsys.component_list:
                    self.selected_subsystem_components_list.append(comp.unique_name)

                break

        for comp in self.detailed_system_model.component_list:

            if self.detailed_model_primary_selection == comp.unique_name:

                self.primary_selection_component = comp

                self.label_detailed_model_params_subsystem.setText("None (Main System)")
                self.label_detailed_model_params_component.setText(self.detailed_model_primary_selection)

                for i in range(0, len(self.detailed_model_param_labels_list)):

                    if i < len(comp.parameter.keys()):
                        param_key = list(comp.parameter.keys())[i]
                        param = comp.parameter[param_key]
                        self.detailed_model_param_labels_list[i].setEnabled(True)
                        self.detailed_model_param_line_edits_list[i].setEnabled(True)
                        self.detailed_model_param_labels_list[i].setText(f"{param_key}:")
                        self.detailed_model_param_line_edits_list[i].setText(str(param))
                    else:
                        self.detailed_model_param_labels_list[i].setEnabled(False)
                        self.detailed_model_param_line_edits_list[i].setEnabled(False)
                        self.detailed_model_param_labels_list[i].setText(f"Parameter {i+1}:")
                        self.detailed_model_param_line_edits_list[i].setText("")

                break

            self.create_detailed_model_network_graph_plot(keep_previous_pos=True)

    def interpret_primary_click_selected_subsystem(self):

        self.primary_selection_component = None
        self.primary_selection_subsystem = None

        for comp in self.current_displayed_subsystem.component_list:

            if self.detailed_model_primary_selection == comp.unique_name:

                self.primary_selection_component = comp

                self.label_detailed_model_params_subsystem.setText(f"{self.current_displayed_subsystem.unique_name}")
                self.label_detailed_model_params_component.setText(self.detailed_model_primary_selection)

                for i in range(0, len(self.detailed_model_param_labels_list)):

                    if i < len(comp.parameter.keys()):
                        param_key = list(comp.parameter.keys())[i]
                        param = comp.parameter[param_key]
                        self.detailed_model_param_labels_list[i].setEnabled(True)
                        self.detailed_model_param_line_edits_list[i].setEnabled(True)
                        self.detailed_model_param_labels_list[i].setText(f"{param_key}:")
                        self.detailed_model_param_line_edits_list[i].setText(str(param))
                    else:
                        self.detailed_model_param_labels_list[i].setEnabled(False)
                        self.detailed_model_param_line_edits_list[i].setEnabled(False)
                        self.detailed_model_param_labels_list[i].setText(f"Parameter {i+1}:")
                        self.detailed_model_param_line_edits_list[i].setText("")

                break

        self.create_selected_subsystem_network_graph_plot(keep_previous_pos=True)

    def update_component_parameters(self):

        if self.primary_selection_component is not None:

            for i in range(0, len(self.detailed_model_param_labels_list)):
                # TODO Update parameters of component
                pass


def _create_matplotlib_figure_groupbox(groupbox: QGroupBox) -> (Figure, Any, FigureCanvas):

    # Result comparison
    fig, ax = plt.subplots(1, 1)

    canvas = FigureCanvas(fig)
    canvas.setParent(groupbox)

    widget = QWidget()
    widget.setLayout(QHBoxLayout())
    widget.layout().setContentsMargins(0, 0, 0, 0)
    widget.layout().setSpacing(0)
    widget.layout().addWidget(canvas)

    nav = NavigationToolbar(canvas, widget, coordinates=False)
    nav.setOrientation(QtCore.Qt.Vertical)
    nav.setStyleSheet("QToolBar { border: 0px }")
    widget.layout().addWidget(nav)

    groupbox.setLayout(widget.layout())

    return fig, ax, canvas


def add_items_to_tree_json_response(parent_item, data: dict):

    components_child_item = QTreeWidgetItem(parent_item)
    components_child_item.setText(0, "Components")

    for component in data["components"]:
        component_child_item = QTreeWidgetItem(components_child_item)
        component_child_item.setText(0, component["id"])

        for idx, port in enumerate(component["ports"]):
            port_item = QTreeWidgetItem(component_child_item)
            port_item.setText(0, f"Port {idx+1}: {port['id']}")

    connections_child_item = QTreeWidgetItem(parent_item)
    connections_child_item.setText(0, "Connections")

    for idx, connection in enumerate(data["connections"]):
        component_child_item = QTreeWidgetItem(connections_child_item)
        component_child_item.setText(0, f"{idx+1}. {connection['from']} -> {connection['to']}")


def add_items_to_tree_abstract_system_model(parent_item, abstract_system_model: AbstractSystem):

    components_child_item = QTreeWidgetItem(parent_item)
    components_child_item.setText(0, "Components")

    for component in abstract_system_model.abstract_components_list:
        component_child_item = QTreeWidgetItem(components_child_item)
        component_child_item.setText(0, component.unique_name)

        for idx, port in enumerate(component.ports_list):
            port_item = QTreeWidgetItem(component_child_item)
            port_item.setText(0, f"Port {idx+1}: {port}")

    connections_child_item = QTreeWidgetItem(parent_item)
    connections_child_item.setText(0, "Connections")

    for idx, connection in enumerate(abstract_system_model.abstract_connections_list):
        connection_child_item = QTreeWidgetItem(connections_child_item)
        connection_child_item.setText(0, f"{connection.from_component} [{connection.from_port}] "
                                         f"-> {connection.to_component} [{connection.to_port}]")


def add_items_to_tree_detailed_system_model(parent_item, detailed_system_model: System):

    components_child_item = QTreeWidgetItem(parent_item)
    components_child_item.setText(0, "Components")

    for component in detailed_system_model.component_list:
        component_child_item = QTreeWidgetItem(components_child_item)
        component_child_item.setText(0, component.unique_name)

        for idx, port in enumerate(component.ports):
            port_item = QTreeWidgetItem(component_child_item)
            port_item.setText(0, f"Port {idx+1}: {port}")

    subsystems_child_item = QTreeWidgetItem(parent_item)
    subsystems_child_item.setText(0, "Subsystems")

    for subsystem in detailed_system_model.subsystem_list:
        subsystem_child_item = QTreeWidgetItem(subsystems_child_item)
        subsystem_child_item.setText(0, subsystem.unique_name)

        subsystem_components_child_item = QTreeWidgetItem(subsystem_child_item)
        subsystem_components_child_item.setText(0, "Subsystem Components")

        for subsystem_component in subsystem.component_list:
            subsystem_component_child_item = QTreeWidgetItem(subsystem_components_child_item)
            subsystem_component_child_item.setText(0, subsystem_component.unique_name)

            for idx, port in enumerate(subsystem_component.ports):
                port_item = QTreeWidgetItem(subsystem_component_child_item)
                port_item.setText(0, f"Port {idx+1}: {port}")

        subsystem_connections_child_item = QTreeWidgetItem(subsystem_child_item)
        subsystem_connections_child_item.setText(0, "Subsystem Connections")

        for subsystem_connection in subsystem.connection_list:
            subsystem_connection_child_item = QTreeWidgetItem(subsystem_connections_child_item)
            subsystem_connection_child_item.setText(0, f"{subsystem_connection.from_block.unique_name} [{subsystem_connection.from_port}] "
                                                       f"-> {subsystem_connection.to_block.unique_name} [{subsystem_connection.to_port}]")

    connections_child_item = QTreeWidgetItem(parent_item)
    connections_child_item.setText(0, "Connections")

    for idx, connection in enumerate(detailed_system_model.connection_list):
        connection_child_item = QTreeWidgetItem(connections_child_item)
        connection_child_item.setText(0, f"{connection.from_block.unique_name} [{connection.from_port}] "
                                         f"-> {connection.to_block.unique_name} [{connection.to_port}]")


def run_thread(target: Callable[[Any], None], worker: PercentageWorker) -> None:

    threading.Thread(
        target=target,
        args=(),
        kwargs=dict(worker=worker),
        daemon=True,
    ).start()
