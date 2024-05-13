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

This module upgrades detailed system models using fault-tolerant design patterns.

Solution built upon code developed by Yu Zhang as part of a master thesis. Used with permission of the
Institute of Industrial Automation and Software Engineering (IAS) as part of the University of Stuttgart.
Source: https://github.com/yuzhang330/simulink-model-generation-and-evolution

Last modification: 25.02.2024
"""

__version__ = "2"
__author__ = "Patrick Hummel, Yu Zhang"

import copy
import math
import random

from src.model.components import CurrentSensorBlock, VoltageSensorBlock
from src.model.system import Subsystem

SINGLE_UPGRADER_COMPARATOR_PATTERN = "comparator"
SINGLE_UPGRADER_VOTER_PATTERN = "voter"
COMBINED_UPGRADER_C_AND_V_PATTERN = "C+V"
COMBINED_UPGRADER_V_AND_C_PATTERN = "V+C"
COMBINED_UPGRADER_C_AND_S_PATTERN = "C+S"
COMBINED_UPGRADER_V_AND_C_AND_S_PATTERN = "V+C+S"


class Upgrader:

    def upgrade(self):
        pass


# Concrete Component
class BasicUpgrader(Upgrader):
    def __init__(self, system):
        self.origin_sys = copy.deepcopy(system)
        self.sys = system

    def upgrade(self):
        return self.sys


class UpgraderDecorator(Upgrader):
    def __init__(self, upgrader):
        self.wrappee = upgrader

    def upgrade(self):
        self.wrappee.upgrade()


class SingleUpgrader(UpgraderDecorator):

    @staticmethod
    def comparator_pattern(subsys: Subsystem, sensors_list_dict: dict):

        for sensor_type in sensors_list_dict.keys():

            if len(sensors_list_dict[sensor_type]) > 0:

                # If there are less than two sensors, add another sensor of the same type
                if len(sensors_list_dict[sensor_type]) < 2:
                    new_sensors = subsys.add_multiple_sensors_like_existing_sensor(existing_sensor=sensors_list_dict[sensor_type][0],
                                                                                   count=1)
                    sensors_list_dict[sensor_type].extend(new_sensors)

                # Add comparator block and connect sensors to it
                subsys.add_comparator_block_and_connections(sensors_list=sensors_list_dict[sensor_type])

    @staticmethod
    def voter_pattern(subsys: Subsystem, sensors_list_dict: dict, target: int):

        # Calculate total number of sensors required
        odd_integer = 2 * target + 1

        for sensor_type in sensors_list_dict.keys():

            if len(sensors_list_dict[sensor_type]) > 0:

                # If there are less than the target (odd_integer) sensors, add another sensor of the same type
                if len(sensors_list_dict[sensor_type]) < odd_integer:
                    new_sensors = subsys.add_multiple_sensors_like_existing_sensor(existing_sensor=sensors_list_dict[sensor_type][0],
                                                                                   count=odd_integer-len(sensors_list_dict[sensor_type]))
                    sensors_list_dict[sensor_type].extend(new_sensors)

                # Add comparator block and connect sensors to it
                subsys.add_voter_block_and_connections(sensors_list=sensors_list_dict[sensor_type])

                subsys.fault_tolerant = (odd_integer - 1)/2

    def upgrade(self, pattern_name=None, subsystem_unique_name=None, target=None):

        # Round up target number
        if target is not None:
            target = math.ceil(target)

        selected_subsystem = None

        for subsys in self.wrappee.sys.subsystem_list:

            if subsys.unique_name == subsystem_unique_name:
                selected_subsystem = subsys
                break

        if selected_subsystem is None:
            raise ValueError(f"No such subsystem found: {subsystem_unique_name}")

        sensors_list_dict = {"current": [], "voltage": []}

        # Go through all components, check for sensor blocks
        for component in selected_subsystem.component_list:

            if isinstance(component, CurrentSensorBlock):
                sensors_list_dict["current"].append(component)
            elif isinstance(component, VoltageSensorBlock):
                sensors_list_dict["voltage"].append(component)

        if pattern_name == SINGLE_UPGRADER_COMPARATOR_PATTERN:
            self.comparator_pattern(selected_subsystem, sensors_list_dict)
        elif pattern_name == SINGLE_UPGRADER_VOTER_PATTERN:
            self.voter_pattern(selected_subsystem, sensors_list_dict, target)
        else:
            raise ValueError(f"{pattern_name} is not a valid single pattern name.")


class CombineUpgrader(UpgraderDecorator):

    @staticmethod
    def c_and_v_pattern(subsys: Subsystem, sensors_list_dict: dict, target: int):

        odd_integer = target + 1

        if odd_integer % 2 == 0:
            odd_integer += 1

        for sensor_type in sensors_list_dict.keys():

            if len(sensors_list_dict[sensor_type]) > 0:

                # If there are less than the target (odd_integer) sensors, add more sensors of the same type
                if len(sensors_list_dict[sensor_type]) < odd_integer * 2:
                    new_sensors = subsys.add_multiple_sensors_like_existing_sensor(
                        existing_sensor=sensors_list_dict[sensor_type][0],
                        count=(odd_integer * 2) - len(sensors_list_dict[sensor_type]))
                    sensors_list_dict[sensor_type].extend(new_sensors)

                # Apply C+V pattern
                subsys.add_c_and_v_pattern(sensors_list_dict[sensor_type])

                subsys.fault_tolerant = odd_integer - 1

    @staticmethod
    def v_and_c_pattern(subsys: Subsystem, sensors_list_dict: dict, target: int):

        odd_integer = target + 2

        if odd_integer % 2 == 0:
            odd_integer += 1

        for sensor_type in sensors_list_dict.keys():

            if len(sensors_list_dict[sensor_type]) > 0:

                # If there are less than the target (odd_integer) sensors, add more sensors of the same type
                if len(sensors_list_dict[sensor_type]) < odd_integer:
                    new_sensors = subsys.add_multiple_sensors_like_existing_sensor(
                        existing_sensor=sensors_list_dict[sensor_type][0], count=odd_integer - len(sensors_list_dict[sensor_type]))
                    sensors_list_dict[sensor_type].extend(new_sensors)

                # Apply V+C pattern
                subsys.add_v_and_c_pattern(sensors_list_dict[sensor_type])

                subsys.fault_tolerant = odd_integer - 2

    @staticmethod
    def c_and_s_pattern(subsys: Subsystem, sensors_list_dict: dict):

        for sensor_type in sensors_list_dict.keys():

            if len(sensors_list_dict[sensor_type]) > 0:

                # TODO Why is this random? can or should it be predefined?
                even_integer = random.randrange(4, 7, 2)

                # If there are less than the target (even_integer) sensors, add more sensors of the same type
                if len(sensors_list_dict[sensor_type]) < even_integer:
                    new_sensors = subsys.add_multiple_sensors_like_existing_sensor(
                        existing_sensor=sensors_list_dict[sensor_type][0],
                        count=even_integer - len(sensors_list_dict[sensor_type]))
                    sensors_list_dict[sensor_type].extend(new_sensors)

                # Apply C+S pattern
                subsys.add_c_and_s_pattern(sensors_list_dict[sensor_type])

    @staticmethod
    def v_and_c_and_s_pattern(subsys: Subsystem, sensors_list_dict: dict, target: int):

        num_integer = target + 2

        odd_integer = random.randrange(3, num_integer + 1, 2)

        for sensor_type in sensors_list_dict.keys():

            if len(sensors_list_dict[sensor_type]) > 0:

                # If there are less than the target (even_integer) sensors, add more sensors of the same type
                if len(sensors_list_dict[sensor_type]) < num_integer:
                    new_sensors = subsys.add_multiple_sensors_like_existing_sensor(
                        existing_sensor=sensors_list_dict[sensor_type][0],
                        count=num_integer - len(sensors_list_dict[sensor_type]))
                    sensors_list_dict[sensor_type].extend(new_sensors)

                # Apply V+C+S pattern
                subsys.add_v_and_c_and_s_pattern(sensors_list_dict[sensor_type], odd_integer=odd_integer)

                subsys.fault_tolerant = num_integer - 2

    def upgrade(self, pattern_name: str = None, subsystem_unique_name: str = None, target: int = None):

        # Round up target number
        if target is not None:
            target = math.ceil(target)

        selected_subsystem = None

        for subsys in self.wrappee.sys.subsystem_list:

            if subsys.unique_name == subsystem_unique_name:
                selected_subsystem = subsys
                break

        if selected_subsystem is None:
            raise ValueError(f"No such subsystem found: {subsystem_unique_name}")

        sensors_list_dict = {"current": [], "voltage": []}

        # Go through all components, check for sensor blocks
        for component in selected_subsystem.component_list:

            if isinstance(component, CurrentSensorBlock):
                sensors_list_dict["current"].append(component)
            elif isinstance(component, VoltageSensorBlock):
                sensors_list_dict["voltage"].append(component)

        if pattern_name == COMBINED_UPGRADER_C_AND_V_PATTERN:
            self.c_and_v_pattern(selected_subsystem, sensors_list_dict, target)
        elif pattern_name == COMBINED_UPGRADER_V_AND_C_PATTERN:
            self.v_and_c_pattern(selected_subsystem, sensors_list_dict, target)
        elif pattern_name == COMBINED_UPGRADER_C_AND_S_PATTERN:
            self.c_and_s_pattern(selected_subsystem, sensors_list_dict)
        elif pattern_name == COMBINED_UPGRADER_V_AND_C_AND_S_PATTERN:
            self.v_and_c_and_s_pattern(selected_subsystem, sensors_list_dict, target)
        else:
            raise ValueError(f"{pattern_name} is not a valid pattern name.")
