# -*- coding: utf-8 -*-

"""
State machine

Last modification: 25.02.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from enum import Enum, auto

from PyQt5.QtCore import QCoreApplication

from src.tools.custom_errors import IllegalStateTransitionError


class State(Enum):

    AWAITING_SPECIFICATION = auto()
    SPECIFICATION_SUMMARIZED = auto()
    ABSTRACT_SYSTEM_MODEL_GENERATED = auto()
    DETAILED_SYSTEM_MODEL_GENERATED = auto()
    SIMSCAPE_MODEL_GENERATED = auto()
    API_ERROR = auto()
    INTERPRETATION_ERROR = auto()
    EXIT = auto()


class StateMachine:

    def __init__(self, window):

        self.current_state = State.AWAITING_SPECIFICATION
        self.last_state = State.AWAITING_SPECIFICATION
        self.window = window

    def set_state(self, new_state: State) -> None:

        valid_transition = False

        if self.current_state == State.AWAITING_SPECIFICATION:

            if new_state == State.SPECIFICATION_SUMMARIZED:
                valid_transition = True
            elif new_state == State.API_ERROR:
                valid_transition = True

        elif self.current_state == State.SPECIFICATION_SUMMARIZED:

            if new_state == State.AWAITING_SPECIFICATION:
                valid_transition = True
            elif new_state == State.ABSTRACT_SYSTEM_MODEL_GENERATED:
                valid_transition = True
            elif new_state == State.API_ERROR:
                valid_transition = True
            elif new_state == State.INTERPRETATION_ERROR:
                valid_transition = True

        elif self.current_state == State.ABSTRACT_SYSTEM_MODEL_GENERATED:

            if new_state == State.DETAILED_SYSTEM_MODEL_GENERATED:
                valid_transition = True
            elif new_state == State.ABSTRACT_SYSTEM_MODEL_GENERATED:
                valid_transition = True
            elif new_state == State.API_ERROR:
                valid_transition = True

        elif self.current_state == State.DETAILED_SYSTEM_MODEL_GENERATED:

            if new_state == State.DETAILED_SYSTEM_MODEL_GENERATED:
                valid_transition = True
            elif new_state == State.SIMSCAPE_MODEL_GENERATED:
                valid_transition = True

        elif self.current_state == State.SIMSCAPE_MODEL_GENERATED:

            if new_state == State.AWAITING_SPECIFICATION:
                valid_transition = True
            elif new_state == State.EXIT:
                valid_transition = True

        elif self.current_state == State.API_ERROR:

            if new_state == State.SPECIFICATION_SUMMARIZED:
                valid_transition = True
            elif new_state == State.ABSTRACT_SYSTEM_MODEL_GENERATED:
                valid_transition = True
            elif new_state == State.EXIT:
                valid_transition = True

        elif self.current_state == State.INTERPRETATION_ERROR:

            if new_state == State.SPECIFICATION_SUMMARIZED:
                valid_transition = True

        else:
            raise ValueError(f"Current state unknown: {self.current_state}")

        # Only proceed with transition (and therefore exit/entry activities) if transition is valid
        if valid_transition:
            self.transition(new_state)
        else:
            raise IllegalStateTransitionError(f"Illegal state transition:{self.current_state.name} -> {new_state.name}")

    def transition(self, new_state: State):

        # Exit activities
        if self.current_state == State.AWAITING_SPECIFICATION:
            pass

        elif self.current_state == State.SPECIFICATION_SUMMARIZED:
            pass

        elif self.current_state == State.ABSTRACT_SYSTEM_MODEL_GENERATED:
            pass

        elif self.current_state == State.DETAILED_SYSTEM_MODEL_GENERATED:
            pass

        elif self.current_state == State.SIMSCAPE_MODEL_GENERATED:
            pass

        elif self.current_state == State.API_ERROR:
            pass

        elif self.current_state == State.INTERPRETATION_ERROR:
            pass

        else:
            raise ValueError(f"Current state unknown: {self.current_state}")

        # Entry activities
        if new_state == State.AWAITING_SPECIFICATION:
            self.window.pushButton_create_specification_summary.setEnabled(True)

        elif new_state == State.SPECIFICATION_SUMMARIZED:
            self.window.pushButton_verify_specification_summary.setEnabled(True)
            self.window.plainTextEdit_specification_summary.setEnabled(True)

        elif new_state == State.ABSTRACT_SYSTEM_MODEL_GENERATED:
            self.window.pushButton_abstract_model_manual_auto_correction.setEnabled(True)
            self.window.pushButton_clear_abstract_model_feedback_text.setEnabled(True)
            self.window.pushButton_abstract_model_send_feedback.setEnabled(True)
            self.window.pushButton_create_detailed_model.setEnabled(True)
            self.window.plainTextEdit_abstract_model_feedback.setEnabled(True)

        elif new_state == State.DETAILED_SYSTEM_MODEL_GENERATED:
            self.window.pushButton_detailed_model_add_component.setEnabled(True)
            self.window.pushButton_detailed_model_add_subsystem.setEnabled(True)
            self.window.pushButton_detailed_model_add_connection.setEnabled(True)
            self.window.pushButton_upgrade_detailed_model.setEnabled(True)
            self.window.pushButton_build_simscape_model.setEnabled(True)

        elif new_state == State.SIMSCAPE_MODEL_GENERATED:
            pass

        elif new_state == State.API_ERROR:

            specific_text = ""

            if self.current_state == State.AWAITING_SPECIFICATION:
                specific_text = "Unable to create a summary of the provided specification."
            elif self.current_state == State.SPECIFICATION_SUMMARIZED:
                specific_text = "Unable to generate an abstract system model."
            elif self.current_state == State.ABSTRACT_SYSTEM_MODEL_GENERATED:
                specific_text = "Unable to improve abstract system model based on feedback."

            # Show error window
            self.window.show_error_dialog(title="API Error", text="An error occurred while trying to access the API.",
                                          informative_text=f"The selected large language model could not be prompted."
                                                         f" {specific_text} Would you like to try again?")

        elif new_state == State.INTERPRETATION_ERROR:

            # Show error window
            self.window.show_error_dialog(title="Interpretation Error", text="An error occurred while trying to interpret the response.",
                                          informative_text=f"The response of the large language model could not be interpreted as an abstract system model. "
                                                         f"Would you like to try again?")
        elif new_state == State.EXIT:

            QCoreApplication.quit()

        else:
            raise ValueError(f"Current state unknown: {new_state}")

        # Complete transition
        self.last_state = self.current_state
        self.current_state = new_state

        self.window.label_info_current_state.setText(self.current_state.name)
