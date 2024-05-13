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

System builder that builds a detailed system model from an abstract system model created by the AI.

Last modification: 01.02.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"

from src.abstract_model.abstract_system import AbstractSystem
from src.model.components import ComponentBlock, SolverBlock, ReferenceBlock
from src.model.system import System, Connection, Subsystem


class SystemBuilder:

    def __init__(self, abstract_system: AbstractSystem):
        self._abstract_system = abstract_system
        self._detailed_system = System()

    @property
    def abstract_system(self) -> AbstractSystem:
        return self._abstract_system

    @property
    def detailed_system(self) -> System:
        return self._detailed_system

    def build(self, name: str) -> System:

        new_system = System(name=name)
        new_component_block_dict = {}
        new_subsystem_dict = {}

        # Go through each abstract component and add it as a component block or subsystem block to the system model
        for abstract_component in self._abstract_system.abstract_components_list:

            new_component_block_type = abstract_component.get_associated_block_type()
            new_component_block = new_component_block_type()

            if isinstance(new_component_block, ComponentBlock):
                new_component_block_dict[abstract_component.unique_name] = new_component_block
                new_system.add_component(new_component_block)

            elif isinstance(new_component_block, Subsystem):
                new_subsystem_dict[abstract_component.unique_name] = new_component_block
                new_component_block.check_connections()
                new_system.add_subsystem(new_component_block)

        # Go through each abstract connection and create a similar connection between the newly added blocks
        for abstract_connection in self._abstract_system.abstract_connections_list:

            from_block = None
            from_port = ""
            to_block = None
            to_port = ""

            if abstract_connection.from_component.unique_name in new_component_block_dict:
                from_block = new_component_block_dict[abstract_connection.from_component.unique_name]

                # TODO Can this be improved? Check which type of port first!
                # Use first output port found
                from_port = from_block.ports[0]

            elif abstract_connection.from_component.unique_name in new_subsystem_dict:
                from_block = new_subsystem_dict[abstract_connection.from_component.unique_name]

                # TODO Can this be improved?
                # Use first output port found
                from_port = from_block.out_ports[0].unique_name

            if abstract_connection.to_component.unique_name in new_component_block_dict:
                to_block = new_component_block_dict[abstract_connection.to_component.unique_name]

                # TODO Can this be improved? Check which type of port first!
                # Use first output port found
                from_port = to_block.ports[0]

            elif abstract_connection.to_component.unique_name in new_subsystem_dict:
                to_block = new_subsystem_dict[abstract_connection.to_component.unique_name]

                # TODO Can this be improved?
                # Use first output port found
                to_port = to_block.in_ports[0].unique_name

            if (not isinstance(from_block, type(None)) and len(from_port) > 0
                    and not isinstance(to_block, type(None)) and len(to_port) > 0):

                new_connection = Connection(from_block=from_block, from_port=from_port, to_block=to_block, to_port=to_port)
                new_system.add_connection(new_connection)

        # Add solver and reference
        solver = SolverBlock()
        new_system.add_component(solver)

        reference = ReferenceBlock()
        new_system.add_component(reference)

        # TODO Let AI choose location of the reference block
        first_subsystem = new_system.subsystem_list[0]
        conn_1 = Connection(from_block=solver, from_port=solver.ports[0], to_block=first_subsystem, to_port=first_subsystem.in_ports[0].unique_name)
        new_system.add_connection(conn_1)
        conn_2 = Connection(from_block=reference, from_port=reference.ports[0], to_block=first_subsystem, to_port=first_subsystem.in_ports[0].unique_name)
        new_system.add_connection(conn_2)

        # Check connections and remove unnecessary port descriptors
        new_system.check_connections()

        self._detailed_system = new_system

        return new_system
