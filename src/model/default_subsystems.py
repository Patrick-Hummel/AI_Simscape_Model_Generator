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

Default subsystem blocks consisting of components and data input from workspace or sensors that output data to workspace.

Last modification: 28.11.2023
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from src.model.system import Subsystem, Connection
from src.model.components import SPSTSwitchBlock, SimuPSConvBlock, FromWorkspaceBlock, ConnectionPortBlock, \
    SPDTSwitchBlock, SPMTSwitchBlock, ControlledVoltageSourceBlock, VoltageSourceDCBlock, VoltageSourceACBlock, \
    ControlledCurrentSourceBlock, CurrentSourceDCBlock, CurrentSourceACBlock, BatteryBlock, UniversalMotorBlock, \
    IncandescentLampBlock, PSSimuConvBlock, ToWorkspaceBlock, ScopeBlock, VoltageSensorBlock, CurrentSensorBlock, \
    InertiaBlock, ResistorBlock, VaristorBlock, CapacitorBlock, InductorBlock, VariableCapacitorBlock, \
    VariableInductorBlock, DiodeBlock, NChannelMOSFETBlock, PChannelMOSFETBlock, NPNBipolarTransistorBlock, \
    PNPBipolarTransistorBlock


class SPMTSwitchSubsystem(Subsystem):

    def __init__(self, threshold: float = 0.5, throw_count: int = 1):
        super().__init__(name=self.__class__.__name__)

        match throw_count:
            case 1: comp_switch = SPSTSwitchBlock(parameters={"Threshold": threshold})
            case 2: comp_switch = SPDTSwitchBlock(parameters={"Threshold": threshold})
            case _: comp_switch = SPMTSwitchBlock(number=throw_count, parameters={"Threshold": threshold})

        self.add_component(comp_switch)

        # Add signal from workspace using a converter block
        self.add_signal_from_workspace(component=comp_switch, signal_port=comp_switch.ports[0])

        comp_connection_port_in = ConnectionPortBlock(parameters={"Orientation": "left", "Side": "left", "_Port_Type": "Inport"})
        self.add_component(comp_connection_port_in)

        # Connections between connection ports and switch
        conn = Connection(from_block=comp_connection_port_in, from_port=comp_connection_port_in.ports[0],
                          to_block=comp_switch, to_port=comp_switch.ports[1])

        self.add_connection(conn)

        # Add a connection port for each 'throw' and connect it to the switch
        for i in range(0, throw_count):

            comp_connection_port_out = ConnectionPortBlock(parameters={"Orientation": "right", "Side": "right", "_Port_Type": "Outport"})
            self.add_component(comp_connection_port_out)

            # Connections between connection ports and switch
            conn = Connection(from_block=comp_switch, from_port=comp_switch.ports[i+2],
                              to_block=comp_connection_port_out, to_port=comp_connection_port_out.ports[0])

            self.add_connection(conn)

        # Check if ports are valid and remove "OUT" and "IN" markers
        self.check_connections()


class SPSTSwitchSubsystem(SPMTSwitchSubsystem):

    def __init__(self, threshold: float = 0.5):
        super().__init__(threshold=threshold, throw_count=1)


class SPDTSwitchSubsystem(SPMTSwitchSubsystem):

    def __init__(self, threshold: float = 0.5):
        super().__init__(threshold=threshold, throw_count=2)


class ElectricalSourceSubsystem(Subsystem):

    def __init__(self, source_type: str = "Voltage", current_type: str = "DC", is_controllable: bool = False):
        super().__init__(name=self.__class__.__name__)

        if source_type == "Voltage":

            if current_type == "DC":

                if is_controllable:
                    comp_source = ControlledVoltageSourceBlock()
                else:
                    comp_source = VoltageSourceDCBlock()

            elif current_type == "AC":

                if is_controllable:
                    comp_source = ControlledVoltageSourceBlock()
                    # TODO Add signal f.e. a sine wave as input?
                else:
                    comp_source = VoltageSourceACBlock()

            else:
                raise ValueError("The current_type must be 'DC' or 'AC'")

        elif source_type == "Current":

            if current_type == "DC":

                if is_controllable:
                    comp_source = ControlledCurrentSourceBlock()
                else:
                    comp_source = CurrentSourceDCBlock()

            elif current_type == "AC":

                if is_controllable:
                    comp_source = ControlledCurrentSourceBlock()
                    # TODO Add signal f.e. a sine wave as input?
                else:
                    comp_source = CurrentSourceACBlock()

            else:
                raise ValueError("The current_type must be 'DC' or 'AC'")

        elif source_type == "Battery":

            comp_source = BatteryBlock()

        else:
            raise ValueError("The source_type must be 'Voltage', 'Current' or 'Battery'")

        self.add_component(comp_source)

        port_in_index = 0
        port_out_index = 1

        if is_controllable:

            # Controlled sources have an additional signal port
            port_in_index = 1
            port_out_index = 2

            # Add signal from workspace using a converter block
            self.add_signal_from_workspace(component=comp_source, signal_port=comp_source.ports[0])

        comp_connection_port_in = ConnectionPortBlock(parameters={"Orientation": "left", "Side": "left", "_Port_Type": "Inport"})
        self.add_component(comp_connection_port_in)

        # Connections between connection ports and source
        conn = Connection(from_block=comp_connection_port_in, from_port=comp_connection_port_in.ports[0],
                          to_block=comp_source, to_port=comp_source.ports[port_in_index])

        self.add_connection(conn)

        comp_connection_port_out = ConnectionPortBlock(
            parameters={"Orientation": "right", "Side": "right", "_Port_Type": "Outport"})
        self.add_component(comp_connection_port_out)

        conn = Connection(from_block=comp_source, from_port=comp_source.ports[port_out_index],
                          to_block=comp_connection_port_out, to_port=comp_connection_port_out.ports[0])

        self.add_connection(conn)

        # Check if ports are valid and remove "OUT" and "IN" markers
        self.check_connections()


class VoltageSourceDCSubsystem(ElectricalSourceSubsystem):
    def __init__(self):
        super().__init__(source_type="Voltage", current_type="DC", is_controllable=False)


class VoltageSourceACSubsystem(ElectricalSourceSubsystem):
    def __init__(self):
        super().__init__(source_type="Voltage", current_type="AC", is_controllable=False)


class ControlledVoltageSourceDCSubsystem(ElectricalSourceSubsystem):
    def __init__(self):
        super().__init__(source_type="Voltage", current_type="DC", is_controllable=True)


class ControlledVoltageSourceACSubsystem(ElectricalSourceSubsystem):
    def __init__(self):
        super().__init__(source_type="Voltage", current_type="AC", is_controllable=True)


class CurrentSourceDCSubsystem(ElectricalSourceSubsystem):
    def __init__(self):
        super().__init__(source_type="Current", current_type="DC", is_controllable=False)


class CurrentSourceACSubsystem(ElectricalSourceSubsystem):
    def __init__(self):
        super().__init__(source_type="Current", current_type="AC", is_controllable=False)


class ControlledCurrentSourceDCSubsystem(ElectricalSourceSubsystem):
    def __init__(self):
        super().__init__(source_type="Current", current_type="DC", is_controllable=True)


class ControlledCurrentSourceACSubsystem(ElectricalSourceSubsystem):
    def __init__(self):
        super().__init__(source_type="Current", current_type="AC", is_controllable=True)


class BatterySubsystem(ElectricalSourceSubsystem):
    def __init__(self):
        super().__init__(source_type="Battery", current_type="DC", is_controllable=False)


class MissionSubsystem(Subsystem):

    def __init__(self, mission_type: str = "Motor"):
        super().__init__(name=self.__class__.__name__)

        match mission_type:

            case "Motor": comp_mission = UniversalMotorBlock()
            case "Lamp": comp_mission = IncandescentLampBlock()
            case "LED": raise NotImplementedError()
            case _: raise ValueError("The mission_type must be 'Motor', 'Lamp' or 'LED'")

        self.add_component(comp_mission)

        if mission_type == "Motor":

            comp_inertia = InertiaBlock()
            self.add_component(comp_inertia)

            conn_mechanical_1 = Connection(from_block=comp_mission, from_port=comp_mission.ports[2],
                                           to_block=comp_inertia, to_port=comp_inertia.ports[0])
            self.add_connection(conn_mechanical_1)

            conn_mechanical_2 = Connection(from_block=comp_inertia, from_port=comp_inertia.ports[1],
                                           to_block=comp_mission, to_port=comp_mission.ports[3])
            self.add_connection(conn_mechanical_2)

        # Connection ports to circuit
        comp_connection_port_in = ConnectionPortBlock(parameters={"Orientation": "left", "Side": "left", "_Port_Type": "Inport"})
        self.add_component(comp_connection_port_in)

        comp_connection_port_out = ConnectionPortBlock(parameters={"Orientation": "right", "Side": "right", "_Port_Type": "Outport"})
        self.add_component(comp_connection_port_out)

        # Add voltage sensor parallel to mission
        self.add_sensor_between(first_comp=comp_mission, first_port=comp_mission.ports[0],
                                second_comp=comp_mission, second_port=comp_mission.ports[1],
                                sensor_type="Voltage", include_scope=True)

        # Add current sensor between connector and mission
        self.add_sensor_between(first_comp=comp_connection_port_in, first_port=comp_connection_port_in.ports[0],
                                second_comp=comp_mission, second_port=comp_mission.ports[0],
                                sensor_type="Current", include_scope=True)

        # Add connection from mission component to output port
        conn_1 = Connection(from_block=comp_mission, from_port=comp_mission.ports[1],
                            to_block=comp_connection_port_out, to_port=comp_connection_port_out.ports[0])

        self.add_connection(conn_1)

        # Check if ports are valid and remove "OUT" and "IN" markers
        self.check_connections()


class MotorMissionSubsystem(MissionSubsystem):

    def __init__(self):
        super().__init__(mission_type="Motor")


class LampMissionSubsystem(MissionSubsystem):

    def __init__(self):
        super().__init__(mission_type="Lamp")


class PassiveElementSubsystem(Subsystem):

    def __init__(self, element_type: str = "Resistor"):
        super().__init__(name=self.__class__.__name__)

        match element_type:

            case "Resistor": comp_element = ResistorBlock()
            case "Varistor": comp_element = VaristorBlock()
            case "Capacitor": comp_element = CapacitorBlock()
            case "VariableCapacitor": comp_element = VariableCapacitorBlock()
            case "Inductor": comp_element = InductorBlock()
            case "VariableInductor": comp_element = VariableInductorBlock()
            case "Diode": comp_element = DiodeBlock()
            case _: raise ValueError("The element_type must be 'Resistor', 'Varistor', 'Capacitor', 'VariableCapacitor', "
                                     "'Inductor', 'VariableInductor' or 'Diode'")

        self.add_component(comp_element)

        port_in_index = 0
        port_out_index = 1

        # If variable, add FromWorkspace block, converter and signal
        if element_type == "VariableCapacitor" or element_type == "VariableInductor":

            # Controlled sources have an additional signal port
            port_in_index = 1
            port_out_index = 2

            # Add signal from workspace using a converter block
            self.add_signal_from_workspace(component=comp_element, signal_port=comp_element.ports[0])

        # Connection ports to circuit
        comp_connection_port_in = ConnectionPortBlock(parameters={"Orientation": "left", "Side": "left", "_Port_Type": "Inport"})
        self.add_component(comp_connection_port_in)

        comp_connection_port_out = ConnectionPortBlock(parameters={"Orientation": "right", "Side": "right", "_Port_Type": "Outport"})
        self.add_component(comp_connection_port_out)

        # Add voltage sensor parallel to element
        self.add_sensor_between(first_comp=comp_element, first_port=comp_element.ports[port_in_index],
                                second_comp=comp_element, second_port=comp_element.ports[port_out_index],
                                sensor_type="Voltage", include_scope=True)

        # Add current sensor between connector and element
        self.add_sensor_between(first_comp=comp_connection_port_in, first_port=comp_connection_port_in.ports[0],
                                second_comp=comp_element, second_port=comp_element.ports[port_in_index],
                                sensor_type="Current", include_scope=True)

        conn_1 = Connection(from_block=comp_element, from_port=comp_element.ports[port_out_index],
                            to_block=comp_connection_port_out, to_port=comp_connection_port_out.ports[0])

        self.add_connection(conn_1)

        # Check if ports are valid and remove "OUT" and "IN" markers
        self.check_connections()


class ResistorSubsystem(PassiveElementSubsystem):

    def __init__(self):
        super().__init__(element_type="Resistor")


class VaristorSubsystem(PassiveElementSubsystem):

    def __init__(self):
        super().__init__(element_type="Varistor")


class CapacitorSubsystem(PassiveElementSubsystem):

    def __init__(self):
        super().__init__(element_type="Capacitor")


class VariableCapacitorSubsystem(PassiveElementSubsystem):

    def __init__(self):
        super().__init__(element_type="VariableCapacitor")


class InductorSubsystem(PassiveElementSubsystem):

    def __init__(self):
        super().__init__(element_type="Inductor")


class VariableInductorSubsystem(PassiveElementSubsystem):

    def __init__(self):
        super().__init__(element_type="VariableInductor")


class DiodeSubsystem(PassiveElementSubsystem):

    def __init__(self):
        super().__init__(element_type="Diode")


class TransistorSubsystem(Subsystem):

    def __init__(self, transistor_type: str = "N_Channel_MOSFET"):
        super().__init__(name=self.__class__.__name__)

        match transistor_type:

            case "N_Channel_MOSFET": comp_transistor = NChannelMOSFETBlock()
            case "P_Channel_MOSFET": comp_transistor = PChannelMOSFETBlock()
            case "NPN_Bipolar_Transistor": comp_transistor = NPNBipolarTransistorBlock()
            case "PNP_Bipolar_Transistor": comp_transistor = PNPBipolarTransistorBlock()
            case _: raise ValueError("The transistor_type must be 'N_Channel_MOSFET', 'P_Channel_MOSFET',"
                                     " 'NPN_Bipolar_Transistor' or 'PNP_Bipolar_Transistor'")

        self.add_component(comp_transistor)

        # Connection ports to circuit
        comp_connection_port_in = ConnectionPortBlock(parameters={"Orientation": "left", "Side": "left", "_Port_Type": "Inport"})
        self.add_component(comp_connection_port_in)

        comp_connection_port_out_1 = ConnectionPortBlock(parameters={"Orientation": "right", "Side": "right", "_Port_Type": "Outport"})
        self.add_component(comp_connection_port_out_1)

        comp_connection_port_out_2 = ConnectionPortBlock(parameters={"Orientation": "right", "Side": "right", "_Port_Type": "Outport"})
        self.add_component(comp_connection_port_out_2)

        # Add current sensor between in port and transistor base
        self.add_sensor_between(first_comp=comp_connection_port_in, first_port=comp_connection_port_in.ports[0],
                                second_comp=comp_transistor, second_port=comp_transistor.ports[0],
                                sensor_type="Current", include_scope=True)

        # Add current sensor between drain and out port
        self.add_sensor_between(first_comp=comp_transistor, first_port=comp_transistor.ports[1],
                                second_comp=comp_connection_port_out_1, second_port=comp_connection_port_out_1.ports[0],
                                sensor_type="Current", include_scope=True)

        # Add voltage sensor between transistor drain and source
        self.add_sensor_between(first_comp=comp_transistor, first_port=comp_transistor.ports[1],
                                second_comp=comp_transistor, second_port=comp_transistor.ports[2],
                                sensor_type="Voltage", include_scope=True)

        conn = Connection(from_block=comp_connection_port_out_2, from_port=comp_connection_port_out_2.ports[0],
                          to_block=comp_transistor, to_port=comp_transistor.ports[2])

        self.add_connection(conn)

        # Check if ports are valid and remove "OUT" and "IN" markers
        self.check_connections()


class NChannelMOSFETSubsystem(TransistorSubsystem):

    def __init__(self):
        super().__init__(transistor_type="N_Channel_MOSFET")


class PChannelMOSFETSubsystem(TransistorSubsystem):

    def __init__(self):
        super().__init__(transistor_type="P_Channel_MOSFET")


class NPNBipolarTransistorSubsystem(TransistorSubsystem):

    def __init__(self):
        super().__init__(transistor_type="NPN_Bipolar_Transistor")


class PNPBipolarTransistorSubsystem(TransistorSubsystem):

    def __init__(self):
        super().__init__(transistor_type="PNP_Bipolar_Transistor")
