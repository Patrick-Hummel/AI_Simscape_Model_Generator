# -*- coding: utf-8 -*-

"""
System builder that builds a detailed system model from an abstract system model created by the AI.

Last modification: 28.11.2023
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

        # TODO Currently, each port may only be used once. This needs to be changed.
        already_used_ports_dict = {}

        # Go through each abstract connection and create a similar connection between the newly added blocks
        for abstract_connection in self._abstract_system.abstract_connections_list:

            from_block = None
            from_port = ""
            to_block = None
            to_port = ""

            if abstract_connection.from_component.unique_name in new_component_block_dict:
                from_block = new_component_block_dict[abstract_connection.from_component.unique_name]

                # Go through all ports of the component and use each one only once
                for out_port in from_block.ports:
                    if from_block.unique_name in already_used_ports_dict:
                        if out_port not in already_used_ports_dict[from_block.unique_name]:
                            from_port = out_port
                            already_used_ports_dict[from_block.unique_name].append(out_port)
                            break
                    else:
                        already_used_ports_dict[from_block.unique_name] = [out_port]
                        from_port = out_port
                        break

            elif abstract_connection.from_component.unique_name in new_subsystem_dict:
                from_block = new_subsystem_dict[abstract_connection.from_component.unique_name]

                # Go through all output ports of the system and use each one only once
                for out_port in from_block.out_ports:
                    if from_block.unique_name in already_used_ports_dict:
                        if out_port.unique_name not in already_used_ports_dict[from_block.unique_name]:
                            from_port = out_port.unique_name
                            already_used_ports_dict[from_block.unique_name].append(out_port.unique_name)
                            break
                    else:
                        from_port = out_port.unique_name
                        already_used_ports_dict[from_block.unique_name] = [out_port.unique_name]
                        break


            if abstract_connection.to_component.unique_name in new_component_block_dict:
                to_block = new_component_block_dict[abstract_connection.to_component.unique_name]

                # Go through all ports of the component and use each one only once
                for in_port in to_block.ports:
                    if to_block.unique_name in already_used_ports_dict:
                        if in_port not in already_used_ports_dict[to_block.unique_name]:
                            to_port = in_port
                            already_used_ports_dict[to_block.unique_name].append(in_port)
                            break
                    else:
                        already_used_ports_dict[to_block.unique_name] = [in_port]
                        to_port = in_port
                        break

            elif abstract_connection.to_component.unique_name in new_subsystem_dict:
                to_block = new_subsystem_dict[abstract_connection.to_component.unique_name]

                # Go through all input ports of the system and use each one only once
                for in_port in to_block.in_ports:
                    if to_block.unique_name in already_used_ports_dict:
                        if in_port.unique_name not in already_used_ports_dict[to_block.unique_name]:
                            to_port = in_port.unique_name
                            already_used_ports_dict[to_block.unique_name].append(in_port.unique_name)
                            break
                    else:
                        to_port = in_port.unique_name
                        already_used_ports_dict[to_block.unique_name] = [in_port.unique_name]
                        break

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
