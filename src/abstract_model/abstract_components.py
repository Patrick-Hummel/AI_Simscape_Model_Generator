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

Abstract components used in the abstract system model generated by the AI.

Last modification: 01.02.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from abc import ABC
from typing import List, Type, Dict

from src.model.components import ComponentBlock, SPSTSwitchBlock, SPDTSwitchBlock, SPMTSwitchBlock, BatteryBlock, \
    VoltageSourceACBlock, VoltageSourceDCBlock, CurrentSourceACBlock, CurrentSourceDCBlock, CapacitorBlock, \
    InductorBlock, ResistorBlock, DiodeBlock, IncandescentLampBlock, UniversalMotorBlock, ReferenceBlock

from src.model.default_subsystems import SPMTSwitchSubsystem, SPSTSwitchSubsystem, SPDTSwitchSubsystem, \
    BatterySubsystem, VoltageSourceACSubsystem, VoltageSourceDCSubsystem, CurrentSourceACSubsystem, \
    CurrentSourceDCSubsystem, ControlledVoltageSourceDCSubsystem, LampMissionSubsystem, MotorMissionSubsystem, \
    ResistorSubsystem, InductorSubsystem, CapacitorSubsystem, VariableInductorSubsystem, NPNBipolarTransistorSubsystem, \
    NChannelMOSFETSubsystem, PNPBipolarTransistorSubsystem, PChannelMOSFETSubsystem

from src.model.system import Subsystem


class AbstractComponent(ABC):

    def __init__(self, comp_id: int, unique_name: str, ports_list: List[str]):
        self._comp_id = comp_id
        self._unique_name = unique_name
        self._ports_list = ports_list

    def __str__(self):
        return self.unique_name

    @property
    def comp_id(self) -> int:
        return self._comp_id

    @property
    def unique_name(self) -> str:
        return self._unique_name

    @property
    def ports_list(self) -> List[str]:
        return self._ports_list

    @staticmethod
    def get_all_subclasses(cls) -> List[Type]:
        all_subclasses = []

        # Get direct subclasses
        direct_subclasses = cls.__subclasses__()

        # Recursively get subclasses of subclasses
        for subclass in direct_subclasses:
            all_subclasses.append(subclass)
            all_subclasses.extend(cls.get_all_subclasses(subclass))

        return all_subclasses

    @classmethod
    def get_implemented_component_types_dict(cls) -> Dict[str, Type]:
        implemented_types_list = [subclass for subclass in cls.get_all_subclasses(cls) if ABC not in subclass.__bases__]

        implemented_types_dict = {}

        for implemented_type in implemented_types_list:
            implemented_types_dict[implemented_type.__name__] = implemented_type

        return implemented_types_dict

    pass

    @classmethod
    def get_associated_block_type(cls) -> Type:

        if hasattr(cls, "ASSOCIATED_BLOCK"):
            return cls.ASSOCIATED_BLOCK
        else:
            raise NotImplementedError(f"Class {cls.__name__} does not have an associated block type.")


class ElectricalSwitch(AbstractComponent, ABC):
    pass


class SPSTSwitch(ElectricalSwitch):
    DESCRIPTION: str = "Electrical single-pole single-throw switch"
    ASSOCIATED_BLOCK: Type[Subsystem] = SPSTSwitchSubsystem


class SPDTSwitch(ElectricalSwitch):
    DESCRIPTION: str = "Electrical single-pole dual-throw switch"
    ASSOCIATED_BLOCK: Type[Subsystem] = SPDTSwitchSubsystem


class SPMTSwitch(ElectricalSwitch):
    DESCRIPTION: str = "Electrical single-pole multiple-throw switch"
    ASSOCIATED_BLOCK: Type[Subsystem] = SPMTSwitchSubsystem


class ElectricalSource(AbstractComponent, ABC):
    pass


class Battery(ElectricalSource):
    DESCRIPTION: str = "Battery with nominal voltage, inner resistance and capacity"
    ASSOCIATED_BLOCK: Type[Subsystem] = ControlledVoltageSourceDCSubsystem


class VoltageSourceAC(ElectricalSource):
    DESCRIPTION: str = "AC voltage source"
    ASSOCIATED_BLOCK: Type[Subsystem] = VoltageSourceACSubsystem


class VoltageSourceDC(ElectricalSource):
    DESCRIPTION: str = "DC voltage source"
    ASSOCIATED_BLOCK: Type[Subsystem] = VoltageSourceDCSubsystem


class CurrentSourceAC(ElectricalSource):
    DESCRIPTION: str = "AC current source"
    ASSOCIATED_BLOCK: Type[Subsystem] = CurrentSourceACSubsystem


class CurrentSourceDC(ElectricalSource):
    DESCRIPTION: str = "DC current source"
    ASSOCIATED_BLOCK: Type[Subsystem] = CurrentSourceDCSubsystem


class ElectricalElement(AbstractComponent, ABC):
    pass


class Capacitor(ElectricalElement):
    DESCRIPTION: str = "A capacitor with capacitance in Farad"
    ASSOCIATED_BLOCK: Type[Subsystem] = CapacitorSubsystem


class Inductor(ElectricalElement):
    DESCRIPTION: str = "An inductor with an inductance in Henry"
    ASSOCIATED_BLOCK: Type[Subsystem] = InductorSubsystem


class Resistor(ElectricalElement):
    DESCRIPTION: str = "A resistor with a resistance in Ohm"
    ASSOCIATED_BLOCK: Type[Subsystem] = ResistorSubsystem


class Diode(ElectricalElement):
    DESCRIPTION: str = "A simple diode"
    ASSOCIATED_BLOCK: Type[ComponentBlock] = DiodeBlock


class NChannelMOSFET(ElectricalElement):
    DESCRIPTION: str = "A n-channel MOSFET transistor"
    ASSOCIATED_BLOCK: Type[Subsystem] = NChannelMOSFETSubsystem


class PChannelMOSFET(ElectricalElement):
    DESCRIPTION: str = "A p-channel MOSFET transistor"
    ASSOCIATED_BLOCK: Type[Subsystem] = PChannelMOSFETSubsystem


class NPNBipolarTransistor(ElectricalElement):
    DESCRIPTION: str = "A NPN bipolar transistor"
    ASSOCIATED_BLOCK: Type[Subsystem] = NPNBipolarTransistorSubsystem


class PNPBipolarTransistor(ElectricalElement):
    DESCRIPTION: str = "A NPN bipolar transistor"
    ASSOCIATED_BLOCK: Type[Subsystem] = PNPBipolarTransistorSubsystem


class Mission(AbstractComponent):
    pass


class Lamp(Mission):
    DESCRIPTION: str = "A regular incandescent lamp"
    ASSOCIATED_BLOCK: Type[Subsystem] = LampMissionSubsystem


class Motor(Mission):
    DESCRIPTION: str = "A universal motor"
    ASSOCIATED_BLOCK: Type[Subsystem] = MotorMissionSubsystem


# class Reference(AbstractComponent):
#     DESCRIPTION: str = "Reference, Ground"
#     ASSOCIATED_BLOCK: Type[ComponentBlock] = ReferenceBlock
