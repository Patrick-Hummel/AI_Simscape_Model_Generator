# -*- coding: utf-8 -*-

"""
This module contains the Container, System, Subsystem and Connection classes.

Solution built upon code originally developed by Yu Zhang as part of a master thesis. Used with permission of
the Institute of Industrial Automation and Software Engineering (IAS) as part of the University of Stuttgart.
Source: https://github.com/yuzhang330/simulink-model-generation-and-evolution

Last modification: 04.04.2024
"""

__version__ = "2"
__author__ = "Patrick Hummel, Yu Zhang"

import json
from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Type

import networkx as nx
from networkx import Graph

from config.gobal_constants import MATLAB_DEFAULT_SOLVER, MATLAB_DEFAULT_STOP_TIME, PATH_DEFAULT_SYSTEM_OUTPUT_JSON
from src.model.components import ComponentBlock, SignalBlock, PortBlock, ResistorBlock, VaristorBlock, DiodeBlock, \
    InductorBlock, VariableInductorBlock, \
    CapacitorBlock, VariableCapacitorBlock, ConnectionPortBlock, FromWorkspaceBlock, VoltageSensorBlock, \
    CurrentSensorBlock, PSSimuConvBlock, ToWorkspaceBlock, ScopeBlock, SimuPSConvBlock, SensorBlock, VoterBlock, \
    MuxBlock, ComparatorBlock, ConstantBlock, CommonSwitchBlock, UnitDelayBlock, SparingBlock


class Connection:

    counter: int = 0

    def __init__(self, from_block, from_port: str, to_block, to_port: str):

        self.from_block = from_block
        self.from_port = from_port

        self.to_block = to_block
        self.to_port = to_port

        # Each instance gets a unique ID
        self.id = Connection.counter
        Connection.counter += 1

    def as_dict(self) -> dict:
        return {"from": f"{self.from_block.unique_name}#{self.from_port}",
                "to": f"{self.to_block.unique_name}#{self.to_port}"}

    def from_port_path(self) -> str:
        return f"{self.from_block.unique_name}/{self.from_port}"

    def to_port_path(self) -> str:
        return f"{self.to_block.unique_name}/{self.to_port}"


class Container:

    def __init__(self, name: str, in_ports: List[PortBlock] = None, out_ports: List[PortBlock] = None,
                 component_list: List[ComponentBlock] = None, connection_list: List[Connection] = None):

        self.name = name

        # Create empty lists if necessary
        if isinstance(in_ports, type(None)):
            self.in_ports = []
        else:
            self.in_ports = in_ports

        if isinstance(out_ports, type(None)):
            self.out_ports = []
        else:
            self.out_ports = out_ports

        if isinstance(component_list, type(None)):
            self.component_list = []
        else:
            self.component_list = component_list

        if isinstance(connection_list, type(None)):
            self.connection_list = []
        else:
            self.connection_list = connection_list

    def change_parameter(self, parameter_name, value):
        if hasattr(self, parameter_name):
            setattr(self, parameter_name, value)
        else:
            raise ValueError(f"{parameter_name} is not a valid parameter.")

    def add_component(self, *components):

        for component in components:

            if isinstance(component, ComponentBlock):

                if isinstance(component, ConnectionPortBlock):
                    if component.port_type == "Inport":
                        self.in_ports.append(component)
                    elif component.port_type == "Outport":
                        self.out_ports.append(component)
                    else:
                        raise ValueError(f"ComponentBlock {component} has no valid port_type attribute!")

                # TODO ID based on system?
                # name_count = sum(1 for c in self.component_list if c.name == component.name)
                #
                # if name_count > 0:
                #     existing_ids = [c.ID for c in self.component_list if c.name == component.name]
                #     max_id = max(existing_ids)
                #     component.ID = max_id + 1

                self.component_list.append(component)

            else:
                raise ValueError("Only instances of Component can be added to component_list.")

    def add_connection(self, *connections):
        for connection in connections:
            if isinstance(connection, Connection):
                self.connection_list.append(connection)
            else:
                raise ValueError("Connections must be of type Connection.")

    def list_components(self):
        return [f"{component.unique_name}" for component in self.component_list]

    def list_connections(self):
        return [f"{connection.from_port} -> {connection.to_port}" for connection in self.connection_list]

    def remove_component_by_unique_name(self, unique_name: str):

        # Find and remove the specified component
        removal_index = self.list_components().index(unique_name)
        self.component_list.pop(removal_index)

        # Find and remove all connections associated with this component
        self.remove_connections_single_component(unique_name)

    def remove_connections_single_component(self, component_unique_name: str):

        connections_for_removal_list = []

        for connection in self.connection_list:

            if (connection.from_block.unique_name == component_unique_name or connection.to_block.unique_name == component_unique_name):
                connections_for_removal_list.append(connection)

        if len(connections_for_removal_list) > 0:
            for conn in connections_for_removal_list:
                self.connection_list.remove(conn)

    def remove_connection_by_component_names(self, first_component_unique_name: str, second_component_unique_name: str):

        connection_for_removal = None

        for connection in self.connection_list:

            if (connection.from_block.unique_name == first_component_unique_name and connection.to_block.unique_name == second_component_unique_name) \
                    or (connection.from_block.unique_name == second_component_unique_name and connection.to_block.unique_name == first_component_unique_name):
                connection_for_removal = connection
                break

        if connection_for_removal is not None:
            self.connection_list.remove(connection_for_removal)
        else:
            print(f"Connection between {first_component_unique_name} and {second_component_unique_name} not found for removal.")

    def check_connections(self):

        # TODO Remove this temporary workaround when the port refactor is complete

        for connection in self.connection_list:

            if "OUT" in connection.from_port:
                connection.from_port = connection.from_port.replace("OUT", "")
            elif "IN" in connection.from_port:
                print(f"WARNING: FromPort {connection.from_port} is defined as an input port!")

            if "IN" in connection.to_port:
                connection.to_port = connection.to_port.replace("IN", "")
            elif "OUT" in connection.to_port:
                print(f"WARNING: ToPort {connection.to_port} is defined as an output port!")

            connection.from_port = connection.from_port.replace("signal", "")
            connection.to_port = connection.to_port.replace("signal", "")

            connection.from_port = connection.from_port.replace("+", "")
            connection.to_port = connection.to_port.replace("+", "")

            connection.from_port = connection.from_port.replace("-", "")
            connection.to_port = connection.to_port.replace("-", "")

            connection.from_port = connection.from_port.replace("scope", "")
            connection.to_port = connection.to_port.replace("scope", "")


class Subsystem(Container):

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
    def get_implemented_default_subsystems_dict(cls) -> Dict[str, Type]:
        implemented_types_list = [subclass for subclass in cls.get_all_subclasses(cls) if ABC not in subclass.__bases__]

        implemented_types_dict = {}

        for implemented_type in implemented_types_list:
            implemented_types_dict[implemented_type.__name__] = implemented_type

        return implemented_types_dict

    counter: int = 0

    def __init__(self, name: str = "NewSubsystem", in_ports: List[PortBlock] = None, out_ports: List[PortBlock] = None,
                 component_list: List[ComponentBlock] = None, connection_list: List[Connection] = None):

        super().__init__(name, in_ports, out_ports, component_list, connection_list)

        self.inport_info = []
        self.outport_info = []
        self.fault_tolerant = 0

        # Each instance gets a unique ID
        self.id = Subsystem.counter
        Subsystem.counter += 1

    @property
    def unique_name(self) -> str:
        return f"{self.name}_{self.id}"

    def load_from_json_data(self, json_data: dict):

        self.name = json_data["id"].split("_")[0]

        # Iterate through components
        for component in json_data.get("components", []):

            implemented_component_types_dict = ComponentBlock.get_implemented_component_types_dict()

            if component["type"] in implemented_component_types_dict:

                if ("parameters" in component) and (isinstance(component["parameters"], Dict)):
                    new_comp = implemented_component_types_dict[component["type"]](parameters=component["parameters"])
                    self.add_component(new_comp)
                else:
                    raise ValueError("Parameters need to be of type dictionary.")
            else:
                raise ValueError(f"Component of type {component['type']} does not exist")

        for connection in json_data.get("connections", []):

            from_block = None
            from_block_str = connection["from"].split("#")[0]
            from_port = connection["from"].split("#")[1]

            to_block = None
            to_block_str = connection["to"].split("#")[0]
            to_port = connection["to"].split("#")[1]

            for comp in self.component_list:
                if comp.unique_name == from_block_str:
                    from_block = comp
                if comp.unique_name == to_block_str:
                    to_block = comp

            if not isinstance(from_block, type(None)) and not isinstance(to_block, type(None)):
                self.add_connection(Connection(from_block, from_port, to_block, to_port))

    def as_dict(self) -> dict:
        return {"id": self.unique_name,
                "components": [comp.as_dict() for comp in self.component_list],
                # "subsystems": [subsystem.as_dict() for subsystem in self.subsystem_list],
                "connections": [connection.as_dict() for connection in self.connection_list],
                # "parameters": self.parameter
                }

    def as_networkx_graph(self) -> Graph:

        system_graph = nx.Graph()

        edges_list = []

        for connection in self.connection_list:
            edges_list.append((connection.from_block.unique_name, connection.to_block.unique_name))

        system_graph.add_edges_from(edges_list)

        components_unique_name_list = [component.unique_name for component in self.component_list]
        included_node_list = list(system_graph.nodes)

        for node in components_unique_name_list:
            if node not in included_node_list:
                system_graph.add_node(node)

        return system_graph

    def list_ports(self):

        for port in self.in_ports:
            port_name = f"{self.name}_{self.id}_inport{port}"
            self.inport_info.append(port_name)

        for port in self.out_ports:
            port_name = f"{self.name}_{self.id}_outport{port}"
            self.outport_info.append(port_name)

    def change_component_parameter(self, parameter_name, parameter_value, component_name, component_id):
        for component in self.component_list:
            if component.name == component_name and component.id == component_id:
                new_component = component
                self.component_list.remove(component)
                if hasattr(new_component, parameter_name):
                    setattr(new_component, parameter_name, parameter_value)
                self.component_list.append(new_component)

    def list_played_components(self) -> list:
        played_ports = [port.replace('signal', '') for instance in self.component_list for port in instance.get_port_info() if 'signal' in port]
        adjacent_ports = []
        for element in played_ports:
            for tup in self.connections:
                if element in tup:
                    index = tup.index(element)
                    adjacent_ports.append(tup[1 - index])
                    break
        connections = []
        for element in adjacent_ports:
            element = '_'.join(element.split('_', 2)[:2])
            temp = []
            for tup in self.connections:
                p_list = [p for p in tup if element in p]
                if p_list:
                    index = tup.index(p_list[0])
                    temp.append(tup[1 - index])
            if len(temp) >= 2:
                connections.append(temp)
        played_components = []
        for connection in connections:
            played_couple = []
            for element in connection:
                name, id_str, _ = element.split('_', 2)
                id = int(id_str[2:])
                for component in self.component_list:
                    if component.name == name and component.id == id:
                        played_couple.append(component)
            played_components.append(played_couple)
        return played_components

    def change_signal(self, name, id, new_name):
        signal = [instance for instance in self.component_list if instance.name == name and instance.id == id
                  and instance.component_type == 'Signal']
        if not signal:
            raise ValueError("There is no such signal component in the system.")
        else:
            index_list = [i for i, instance in enumerate(self.component_list) if instance == signal[0]]
            found = False
            for cls in SignalBlock.__subclasses__():
                if cls().name == new_name:
                    new_signal = cls()
                    if len(new_signal.port) == len(signal[0].port):
                        self.add_component(new_signal)
                        new_connections = []
                        old_ports_map = dict(zip(signal[0].get_port_info(), new_signal.get_port_info()))
                        for pair in self.connections:
                            first_element = pair[0] if pair[0] not in old_ports_map else old_ports_map[pair[0]]
                            second_element = pair[1] if pair[1] not in old_ports_map else old_ports_map[pair[1]]
                            new_connections.append((first_element, second_element))
                        self.connections = new_connections
                        self.component_list.pop(index_list[0])
                        found = True
                    else:
                        raise ValueError("The number of ports do not match.")
            if not found:
                raise ValueError("There is no such new signal component.")

    def change_workspace(self, id, variable_name):
        found = False
        for instance in self.component_list:
            if instance.name == 'FromWorkspace' and instance.id == id:
                instance.variable_name = variable_name
                found = True
        if not found:
            raise ValueError("There is no such FromWorkspace component.")

    def filter_connections(self, port_list) -> List:

        result = []

        for element in port_list:
            filter_connections = [t for t in self.connection_list if (element == t.from_port) or (element == t.to_port)]
            result.append(filter_connections)

        return result

    def add_sensor_between(self, first_comp, first_port: str, second_comp, second_port: str,
                           sensor_type: str = "Voltage", include_scope: bool = True) -> SensorBlock:
        """
        This method will add a VoltageSensor block or a CurrentSensor block between the specified components (and ports).
        Additionally, a ToWorkspace block and PS-Simulink Converter block is added to turn the output signal of the
        respective sensor into data that can be accesses via variable from the MATLAB workspace. A Scope block can
        optionally be added for easy analysis in Simulink.

        :param first_comp: The first component to which one end of the sensor is attached.
        :param first_port: The electrical port of the first component.
        :param second_comp: The second component to which the other end of the sensor is attached.
        :param second_port: The electrical port of the second component.
        :param sensor_type: Either 'Voltage' or 'Current'
        :param include_scope: If true, a Scope block is added.
        """

        match sensor_type:
            case "Voltage":
                comp_sensor = VoltageSensorBlock()
            case "Current":
                comp_sensor = CurrentSensorBlock()
            case _:
                raise ValueError("The sensor_type must be 'Voltage' or 'Current'")

        self.add_component(comp_sensor)

        comp_ps_simu_conv = PSSimuConvBlock()
        self.add_component(comp_ps_simu_conv)

        comp_to_workspace = ToWorkspaceBlock(sample_time=0)
        comp_to_workspace.set_unique_variable_name(subsys_id=self.id, component_unique_name=comp_sensor.unique_name)
        self.add_component(comp_to_workspace)

        # Signal from sensor to workspace and scope (optionally) via converter
        conn_signal_1 = Connection(from_block=comp_ps_simu_conv, from_port=comp_ps_simu_conv.ports[1],
                                   to_block=comp_to_workspace, to_port=comp_to_workspace.ports[0])
        self.add_connection(conn_signal_1)

        conn_signal_2 = Connection(from_block=comp_sensor, from_port=comp_sensor.ports[0],
                                   to_block=comp_ps_simu_conv, to_port=comp_ps_simu_conv.ports[0])
        self.add_connection(conn_signal_2)

        # Attach a scope block if required
        if include_scope:

            comp_scope = ScopeBlock()
            self.add_component(comp_scope)

            conn_signal_3 = Connection(from_block=comp_ps_simu_conv, from_port=comp_ps_simu_conv.ports[1],
                                       to_block=comp_scope, to_port=comp_scope.ports[0])
            self.add_connection(conn_signal_3)

        # Connect sensor to first and second component
        conn_1 = Connection(from_block=first_comp, from_port=first_port,
                            to_block=comp_sensor, to_port=comp_sensor.ports[2])

        self.add_connection(conn_1)

        conn_2 = Connection(from_block=comp_sensor, from_port=comp_sensor.ports[1],
                            to_block=second_comp, to_port=second_port)

        self.add_connection(conn_2)

        return comp_sensor

    def add_multiple_sensors_like_existing_sensor(self, existing_sensor: SensorBlock, count: int) -> List[SensorBlock]:

        if isinstance(existing_sensor, CurrentSensorBlock):
            sensor_type = "Current"
        elif isinstance(existing_sensor, VoltageSensorBlock):
            sensor_type = "Voltage"
        else:
            raise ValueError(f"Unknown sensor type {type(existing_sensor)}")

        other_from_block = None
        other_from_port = None
        other_to_block = None
        other_to_port = None

        new_sensors_list = []

        for conn in self.connection_list:

            if (conn.from_block.unique_name == existing_sensor.unique_name) and (
                    not isinstance(conn.to_block, PSSimuConvBlock)):
                other_to_block = conn.to_block
                other_to_port = conn.to_port

            if conn.to_block.unique_name == existing_sensor.unique_name:
                other_from_block = conn.from_block
                other_from_port = conn.from_port

            if other_from_block and other_from_port and other_to_block and other_to_port:
                break

        for x in range(0, count):

            # TODO Current sensors must be in series
            # Add voltage sensor at same ports as existing sensor (in parallel)
            new_sensor = self.add_sensor_between(first_comp=other_from_block, first_port=other_from_port,
                                                 second_comp=other_to_block, second_port=other_to_port,
                                                 sensor_type=sensor_type, include_scope=False)

            new_sensors_list.append(new_sensor)

        return new_sensors_list

    def add_all_sensor_pssimuconv_to_block(self, sensor_list: List, target_block: ComponentBlock):

        port_index = 0

        for sens in sensor_list:

            for conn in self.connection_list:

                if conn.from_block.unique_name == sens.unique_name and isinstance(conn.to_block, PSSimuConvBlock):

                    conn_signal_2 = Connection(from_block=conn.to_block, from_port=conn.to_block.ports[1],
                                               to_block=target_block, to_port=target_block.ports[port_index])
                    self.add_connection(conn_signal_2)

                    port_index += 1

                    break

    def add_comparator_block_and_connections(self, sensors_list: List):

        # Add comparator block and new to workspace block
        comparator_block = ComparatorBlock()
        to_workspace_block = ToWorkspaceBlock()
        to_workspace_block.set_unique_variable_name(subsys_id=self.id, component_unique_name=comparator_block.unique_name)

        self.add_component(comparator_block, to_workspace_block)

        # Signal from comparator to workspace
        conn_signal_1 = Connection(from_block=comparator_block, from_port=comparator_block.ports[2],
                                   to_block=to_workspace_block, to_port=to_workspace_block.ports[0])
        self.add_connection(conn_signal_1)

        # Add output connections from PSSimuConv blocks to the target block inputs
        self.add_all_sensor_pssimuconv_to_block(sensor_list=sensors_list, target_block=comparator_block)

        self.check_connections()

    def add_voter_block_and_connections(self, sensors_list: List):

        # Add comparator block and new to workspace block
        voter_block = VoterBlock()
        mux_block = MuxBlock()
        to_workspace_block = ToWorkspaceBlock()
        to_workspace_block.set_unique_variable_name(subsys_id=self.id, component_unique_name=mux_block.unique_name)

        mux_block.set_input(len(sensors_list))
        self.add_component(voter_block, mux_block, to_workspace_block)

        # Signal from mux to voter
        conn_signal_1 = Connection(from_block=mux_block, from_port=mux_block.ports[-1],
                                   to_block=voter_block, to_port=voter_block.ports[0])
        self.add_connection(conn_signal_1)

        # Signal from voter to workspace
        conn_signal_2 = Connection(from_block=voter_block, from_port=voter_block.ports[1],
                                   to_block=to_workspace_block, to_port=to_workspace_block.ports[0])
        self.add_connection(conn_signal_2)

        # Add output connections from PSSimuConv blocks to the target block inputs
        self.add_all_sensor_pssimuconv_to_block(sensor_list=sensors_list, target_block=mux_block)

        self.check_connections()

    def add_c_and_v_pattern(self, sensors_list: List):

        # Add comparator block and new to workspace block
        voter_block = VoterBlock()
        mux_block = MuxBlock()
        to_workspace_block = ToWorkspaceBlock()
        to_workspace_block.set_unique_variable_name(subsys_id=self.id, component_unique_name=mux_block.unique_name)

        mux_block.set_input(len(sensors_list))
        self.add_component(voter_block, mux_block, to_workspace_block)

        # Signal from mux to voter
        conn_signal_1 = Connection(from_block=mux_block, from_port=mux_block.ports[-1],
                                   to_block=voter_block, to_port=voter_block.ports[0])
        self.add_connection(conn_signal_1)

        # Signal from voter to workspace
        conn_signal_2 = Connection(from_block=voter_block, from_port=voter_block.ports[1],
                                   to_block=to_workspace_block, to_port=to_workspace_block.ports[0])
        self.add_connection(conn_signal_2)

        signal_block = ConstantBlock()
        signal_block.value = 'nan'
        self.add_component(signal_block)

        new_list = [[sensors_list[i], sensors_list[i + 1]] for i in range(0, len(sensors_list), 2)]

        for i, new_pair in enumerate(new_list):

            comparator_block = ComparatorBlock()
            common_switch_block = CommonSwitchBlock()

            self.add_component(comparator_block, common_switch_block)

            # Signal from comparator to common switch block
            conn_signal_1 = Connection(from_block=comparator_block, from_port=comparator_block.ports[2],
                                       to_block=common_switch_block, to_port=common_switch_block.ports[1])
            self.add_connection(conn_signal_1)

            conn_signal_2 = Connection(from_block=signal_block, from_port=signal_block.ports[0],
                                       to_block=common_switch_block, to_port=common_switch_block.ports[2])
            self.add_connection(conn_signal_2)

            conn_signal_3 = Connection(from_block=common_switch_block, from_port=common_switch_block.ports[-1],
                                       to_block=mux_block, to_port=mux_block.ports[i])
            self.add_connection(conn_signal_3)

            for n, new_sensor in enumerate(new_pair):

                for conn in self.connection_list:

                    if conn.from_block.unique_name == new_sensor.unique_name and isinstance(conn.to_block,
                                                                                            PSSimuConvBlock):
                        conn_signal_4 = Connection(from_block=conn.to_block, from_port=conn.to_block.ports[1],
                                                   to_block=comparator_block, to_port=comparator_block.ports[n])
                        self.add_connection(conn_signal_4)

                        if n == 0:
                            conn_signal_5 = Connection(from_block=conn.to_block, from_port=conn.to_block.ports[1],
                                                       to_block=common_switch_block,
                                                       to_port=common_switch_block.ports[0])
                            self.add_connection(conn_signal_5)

                        break

        self.check_connections()

    def add_v_and_c_pattern(self, sensors_list: List):

        # Add voter block and new to workspace block
        voter_block = VoterBlock()
        mux_block = MuxBlock()
        to_workspace_block = ToWorkspaceBlock()
        to_workspace_block.set_unique_variable_name(subsys_id=self.id, component_unique_name=mux_block.unique_name)
        unit_delay_out_block = UnitDelayBlock()

        mux_block.set_input(len(sensors_list))
        self.add_component(voter_block, mux_block, to_workspace_block, unit_delay_out_block)

        # Signal from mux to voter
        conn_signal_1 = Connection(from_block=mux_block, from_port=mux_block.ports[-1],
                                   to_block=voter_block, to_port=voter_block.ports[0])
        self.add_connection(conn_signal_1)

        # Signal from voter to workspace
        conn_signal_2 = Connection(from_block=voter_block, from_port=voter_block.ports[1],
                                   to_block=to_workspace_block, to_port=to_workspace_block.ports[0])
        self.add_connection(conn_signal_2)

        # Signal from voter to workspace
        conn_signal_3 = Connection(from_block=voter_block, from_port=voter_block.ports[1],
                                   to_block=unit_delay_out_block, to_port=unit_delay_out_block.ports[0])
        self.add_connection(conn_signal_3)

        signal_block = ConstantBlock()
        signal_block.value = 'nan'
        self.add_component(signal_block)

        for i, new_sensor in enumerate(sensors_list):

            comparator_block = ComparatorBlock()
            common_switch_block = CommonSwitchBlock()
            unit_delay_block = UnitDelayBlock()

            self.add_component(comparator_block, common_switch_block, unit_delay_block)

            # Signal from comparator to common switch block
            conn_signal_1 = Connection(from_block=comparator_block, from_port=comparator_block.ports[2],
                                       to_block=common_switch_block, to_port=common_switch_block.ports[1])
            self.add_connection(conn_signal_1)

            conn_signal_2 = Connection(from_block=signal_block, from_port=signal_block.ports[0],
                                       to_block=common_switch_block, to_port=common_switch_block.ports[2])
            self.add_connection(conn_signal_2)

            conn_signal_3 = Connection(from_block=common_switch_block,
                                       from_port=common_switch_block.ports[-1],
                                       to_block=mux_block, to_port=mux_block.ports[i])
            self.add_connection(conn_signal_3)

            for conn in self.connection_list:

                if conn.from_block.unique_name == new_sensor.unique_name and isinstance(conn.to_block,
                                                                                        PSSimuConvBlock):
                    conn_signal_4 = Connection(from_block=conn.to_block, from_port=conn.to_block.ports[1],
                                               to_block=common_switch_block, to_port=common_switch_block.ports[0])
                    self.add_connection(conn_signal_4)

                    conn_signal_5 = Connection(from_block=conn.to_block, from_port=conn.to_block.ports[1],
                                               to_block=unit_delay_block, to_port=unit_delay_block.ports[0])
                    self.add_connection(conn_signal_5)

                    break

            conn_signal_6 = Connection(from_block=unit_delay_block, from_port=unit_delay_block.ports[1],
                                       to_block=comparator_block, to_port=comparator_block.ports[0])
            self.add_connection(conn_signal_6)

            conn_signal_7 = Connection(from_block=unit_delay_out_block, from_port=unit_delay_out_block.ports[1],
                                       to_block=comparator_block, to_port=comparator_block.ports[1])
            self.add_connection(conn_signal_7)

    def add_c_and_s_pattern(self, sensors_list: List):

        mux_block = MuxBlock()
        mux_signal_block = MuxBlock()
        sparing_block = SparingBlock()
        to_workspace_block = ToWorkspaceBlock()
        to_workspace_block.set_unique_variable_name(subsys_id=self.id, component_unique_name=mux_block.unique_name)

        mux_signal_block.set_input(int(len(sensors_list) / 2))
        mux_block.set_input(int(len(sensors_list) / 2))

        self.add_component(mux_block, mux_signal_block, to_workspace_block, sparing_block)

        # Signal from voter to workspace
        conn_signal_1 = Connection(from_block=sparing_block, from_port=sparing_block.ports[2],
                                   to_block=to_workspace_block, to_port=to_workspace_block.ports[0])
        self.add_connection(conn_signal_1)

        conn_signal_2 = Connection(from_block=mux_signal_block, from_port=mux_signal_block.ports[-1],
                                   to_block=sparing_block, to_port=sparing_block.ports[0])
        self.add_connection(conn_signal_2)

        conn_signal_3 = Connection(from_block=mux_block, from_port=mux_block.ports[-1],
                                   to_block=sparing_block, to_port=sparing_block.ports[1])
        self.add_connection(conn_signal_3)

        new_list = [[sensors_list[i], sensors_list[i + 1]] for i in range(0, len(sensors_list), 2)]

        for i, new_pair in enumerate(new_list):

            comparator_block = ComparatorBlock()
            self.add_component(comparator_block)

            conn_signal_4 = Connection(from_block=comparator_block, from_port=comparator_block.ports[-1],
                                       to_block=mux_block, to_port=mux_block.ports[i])
            self.add_connection(conn_signal_4)

            for n, new_sensor in enumerate(new_pair):

                for conn in self.connection_list:

                    if conn.from_block.unique_name == new_sensor.unique_name and isinstance(conn.to_block,
                                                                                            PSSimuConvBlock):
                        conn_signal_5 = Connection(from_block=conn.to_block, from_port=conn.to_block.ports[1],
                                                   to_block=comparator_block, to_port=comparator_block.ports[n])
                        self.add_connection(conn_signal_5)

                        if n == 0:
                            conn_signal_6 = Connection(from_block=conn.to_block, from_port=conn.to_block.ports[1],
                                                       to_block=mux_signal_block, to_port=mux_signal_block.ports[i])
                            self.add_connection(conn_signal_6)

                        break

    def add_v_and_c_and_s_pattern(self, sensors_list: List, odd_integer: int):

        mux_signal_block = MuxBlock()
        mux_error_block = MuxBlock()

        sparing_block = SparingBlock()
        sparing_block.n = odd_integer

        voter_block = VoterBlock()

        delay_out_block = UnitDelayBlock()

        to_workspace_block = ToWorkspaceBlock()
        to_workspace_block.set_unique_variable_name(subsys_id=self.id, component_unique_name=voter_block.unique_name)

        mux_signal_block.set_input(len(sensors_list))
        mux_error_block.set_input(len(sensors_list))

        self.add_component(mux_signal_block, mux_error_block, voter_block, sparing_block, delay_out_block, to_workspace_block)

        # Signal from voter to workspace
        conn_signal_1 = Connection(from_block=voter_block, from_port=voter_block.ports[2],
                                   to_block=to_workspace_block, to_port=to_workspace_block.ports[0])
        self.add_connection(conn_signal_1)

        # Signal from voter to delay out
        conn_signal_2 = Connection(from_block=voter_block, from_port=voter_block.ports[2],
                                   to_block=delay_out_block, to_port=delay_out_block.ports[0])
        self.add_connection(conn_signal_2)

        # Signal from sparing to voter
        conn_signal_3 = Connection(from_block=sparing_block, from_port=sparing_block.ports[-1],
                                   to_block=voter_block, to_port=voter_block.ports[0])
        self.add_connection(conn_signal_3)

        # Signal from mux signal to sparing
        conn_signal_4 = Connection(from_block=mux_signal_block, from_port=mux_signal_block.ports[-1],
                                   to_block=sparing_block, to_port=sparing_block.ports[0])
        self.add_connection(conn_signal_4)

        # Signal from mux error to sparing
        conn_signal_5 = Connection(from_block=mux_error_block, from_port=mux_error_block.ports[-1],
                                   to_block=sparing_block, to_port=sparing_block.ports[1])
        self.add_connection(conn_signal_5)

        for i, new_sensor in enumerate(sensors_list):

            comparator_block = ComparatorBlock()
            unit_delay_block = UnitDelayBlock()

            self.add_component(comparator_block, unit_delay_block)

            # Signal from mux error to sparing
            conn_signal_5 = Connection(from_block=comparator_block, from_port=comparator_block.ports[-1],
                                       to_block=mux_error_block, to_port=mux_error_block.ports[i])
            self.add_connection(conn_signal_5)

            for conn in self.connection_list:

                if conn.from_block.unique_name == new_sensor.unique_name and isinstance(conn.to_block,
                                                                                        PSSimuConvBlock):
                    conn_signal_6 = Connection(from_block=conn.to_block, from_port=conn.to_block.ports[1],
                                               to_block=mux_signal_block, to_port=mux_signal_block.ports[i])
                    self.add_connection(conn_signal_6)

                    conn_signal_7 = Connection(from_block=conn.to_block, from_port=conn.to_block.ports[1],
                                               to_block=unit_delay_block, to_port=unit_delay_block.ports[0])
                    self.add_connection(conn_signal_7)

                    conn_signal_8 = Connection(from_block=unit_delay_block, from_port=unit_delay_block.ports[-1],
                                               to_block=comparator_block, to_port=comparator_block.ports[0])
                    self.add_connection(conn_signal_8)

                    conn_signal_8 = Connection(from_block=delay_out_block, from_port=delay_out_block.ports[-1],
                                               to_block=comparator_block, to_port=comparator_block.ports[1])
                    self.add_connection(conn_signal_8)

                    break

    def add_signal_from_workspace(self, component, signal_port: str):
        """
        This method adds a FromWorkspace block and a Simulink-PS Converter block to the subsystem and connects them.
        The signal from the Simulink-PS Converter block is then connected to the specified component and port.

        :param component: Component block to which a signal is to be added
        :param signal_port: The signal input port of the specified component
        """

        comp_simu_ps_conv = SimuPSConvBlock()
        self.add_component(comp_simu_ps_conv)

        workspace_variable_unique_name = f"Subsystem_{self.id}_{component.unique_name}_simin_0"
        comp_from_workspace = FromWorkspaceBlock(variable_name=workspace_variable_unique_name, sample_time=0)
        self.add_component(comp_from_workspace)

        # Signal connection to switch
        conn_signal_1 = Connection(from_block=comp_simu_ps_conv, from_port=comp_simu_ps_conv.ports[1],
                                   to_block=component, to_port=signal_port)
        self.add_connection(conn_signal_1)

        conn_signal_2 = Connection(from_block=comp_from_workspace, from_port=comp_from_workspace.ports[0],
                                   to_block=comp_simu_ps_conv, to_port=comp_simu_ps_conv.ports[0])
        self.add_connection(conn_signal_2)


class System(Container):
    def __init__(self, name: str = "NewSystem", in_ports: List[PortBlock] = None, out_ports: List[PortBlock] = None,
                 component_list: List[ComponentBlock] = None, connection_list: List[Connection] = None,
                 solver: str = MATLAB_DEFAULT_SOLVER, stop_time: int = MATLAB_DEFAULT_STOP_TIME):

        super().__init__(name, in_ports, out_ports, component_list, connection_list)

        self.subsystem_list = []
        self.solver = solver
        self.stop_time = stop_time

    @property
    def parameter(self) -> dict:
        return {'Solver': self.solver, 'StopTime': self.stop_time}

    def as_dict(self):
        return {"name": self.name,
                "components": [comp.as_dict() for comp in self.component_list],
                "subsystems": [subsystem.as_dict() for subsystem in self.subsystem_list],
                "connections": [connection.as_dict() for connection in self.connection_list],
                "parameters": self.parameter}

    # TODO Improve by moving this to the super class (Container)
    def as_networkx_graph(self) -> Graph:

        system_graph = nx.Graph()

        edges_list = []

        for connection in self.connection_list:
            edges_list.append((connection.from_block.unique_name, connection.to_block.unique_name))

        system_graph.add_edges_from(edges_list)

        components_unique_name_list = [component.unique_name for component in self.component_list]
        components_unique_name_list.extend(
            [subsystem.unique_name for subsystem in self.subsystem_list])
        included_node_list = list(system_graph.nodes)

        for node in components_unique_name_list:
            if node not in included_node_list:
                system_graph.add_node(node)

        return system_graph

    def save_as_json(self, output_directory: Path = None):

        if isinstance(output_directory, type(None)):
            output_directory = PATH_DEFAULT_SYSTEM_OUTPUT_JSON

        # Include current date in filename
        datetime_now = datetime.now()
        datetime_now_str = datetime_now.strftime("%Y%m%d_%H%M")

        output_filepath = output_directory / f"system_{self.name}_{datetime_now_str}.json"

        # Write the dictionary to a JSON file with indentation
        with open(output_filepath, 'w') as json_file:
            json.dump(self.as_dict(), json_file, indent=4)

    def load_from_json_data(self, json_data: dict):

        self.name = json_data["name"]

        new_comp_dict = {}
        new_subsys_dict = {}

        # Iterate through components
        for component in json_data.get("components", []):

            implemented_component_types_dict = ComponentBlock.get_implemented_component_types_dict()

            if component["type"] in implemented_component_types_dict:

                if ("parameters" in component) and (isinstance(component["parameters"], Dict)):
                    new_comp = implemented_component_types_dict[component["type"]](parameters=component["parameters"])
                    self.add_component(new_comp)

                    # Remember ID for connections as it may be different from newly generated ID
                    new_comp_dict[component["id"]] = new_comp

                else:
                    raise ValueError("Parameters need to be of type dictionary.")
            else:
                raise ValueError(f"Component of type {component['type']} does not exist")

        for subsystem in json_data.get("subsystems", []):

            new_subsystem = Subsystem()
            new_subsystem.load_from_json_data(subsystem)
            self.add_subsystem(new_subsystem)

            # Remember ID for connections as it may be different from newly generated ID
            new_subsys_dict[subsystem["id"]] = new_subsystem

        for connection in json_data.get("connections", []):

            from_block = None
            from_block_str = connection["from"].split("#")[0]
            from_port = connection["from"].split("#")[1]

            to_block = None
            to_block_str = connection["to"].split("#")[0]
            to_port = connection["to"].split("#")[1]

            if from_block_str in new_comp_dict:
                from_block = new_comp_dict[from_block_str]
            elif from_block_str in new_subsys_dict:
                from_block = new_subsys_dict[from_block_str]

            if to_block_str in new_comp_dict:
                to_block = new_comp_dict[to_block_str]
            elif to_block_str in new_subsys_dict:
                to_block = new_subsys_dict[to_block_str]

            if not isinstance(from_block, type(None)) and not isinstance(to_block, type(None)):
                self.add_connection(Connection(from_block, from_port, to_block, to_port))

        if ("parameters" in json_data) and (isinstance(json_data["parameters"], Dict)):
            self.solver = json_data["parameters"]["Solver"]
            self.stop_time = json_data["parameters"]["StopTime"]

    def add_subsystem(self, *subsystems):
        for subsystem in subsystems:
            if isinstance(subsystem, Subsystem):

                # name_count = sum(1 for s in self.subsystem_list if s.subsystem_type == subsystem.subsystem_type)
                # if name_count > 0:
                #     existing_ids = [sub.id for sub in self.subsystem_list]
                #     max_id = max(existing_ids)
                #     subsystem.id = max_id + 1

                subsystem.list_ports()
                self.subsystem_list.append(subsystem)
            else:
                raise ValueError("Only instances of Subsystem can be added to the subsystem_list.")

    def list_subsystems(self) -> list:
        return [f"{subsystem.unique_name}" for subsystem in self.subsystem_list]

    def remove_subsystem_by_unique_name(self, unique_name: str):

        # Find and remove specified subsystem
        removal_index = self.list_subsystems().index(unique_name)
        self.subsystem_list.pop(removal_index)

        # Find and remove all connections associated with this component
        self.remove_connections_single_component(unique_name)

    def change_component_parameter(self, parameter_name, parameter_value, component_name, component_id,
                                   subsystem_type=None, subsystem_id=None):
        if subsystem_type and subsystem_id is not None:
            for subsys in self.subsystem_list:
                if subsys.subsystem_type == subsystem_type and subsys.id == subsystem_id:
                    new_subsys = subsys
                    self.subsystem_list.remove(subsys)
                    for component in new_subsys.component_list:
                        if component.name == component_name and component.id == component_id:
                            new_component = component
                            new_subsys.component_list.remove(component)
                            if hasattr(new_component, parameter_name):
                                setattr(new_component, parameter_name, parameter_value)
                            new_subsys.component_list.append(new_component)
                    self.subsystem_list.append(new_subsys)
        else:
            for component in self.component_list:
                if component.name == component_name and component.id == component_id:
                    new_component = component
                    self.component_list.remove(component)
                    if hasattr(new_component, parameter_name):
                        setattr(new_component, parameter_name, parameter_value)
                    self.component_list.append(new_component)

    def change_workspace(self, id, variable_name, subsystem_type=None, subsystem_id=None):
        if subsystem_type and subsystem_id is not None:
            for subsys in self.subsystem_list:
                if subsys.subsystem_type == subsystem_type and subsys.id == subsystem_id:
                    new_subsys = subsys
                    self.subsystem_list.remove(subsys)
                    new_subsys.change_workspace(id, variable_name)
                    self.subsystem_list.append(new_subsys)
        else:
            found = False
            for instance in self.component_list:
                if instance.name == 'FromWorkspace' and instance.id == id:
                    instance.variable_name = variable_name
                    found = True
            if not found:
                raise ValueError("There is no such FromWorkspace component.")

    def change_signal(self, name, id, new_name, subsystem_type=None, subsystem_id=None):
        if subsystem_type and subsystem_id is not None:
            for subsys in self.subsystem_list:
                if subsys.subsystem_type == subsystem_type and subsys.id == subsystem_id:
                    new_subsys = subsys
                    self.subsystem_list.remove(subsys)
                    new_subsys.change_signal(name, id, new_name)
                    self.subsystem_list.append(new_subsys)
        else:
            signal = [instance for instance in self.component_list if instance.name == name and instance.id == id
                      and instance.component_type == 'Signal']
            if not signal:
                raise ValueError("There is no such signal component in the system.")
            else:
                index_list = [i for i, instance in enumerate(self.component_list) if instance == signal[0]]
                found = False
                for cls in SignalBlock.__subclasses__():
                    if cls().name == new_name:
                        new_signal = cls()
                        if len(new_signal.port) == len(signal[0].port):
                            self.add_component(new_signal)
                            new_connections = []
                            old_ports_map = dict(zip(signal[0].get_port_info(), new_signal.get_port_info()))
                            for pair in self.connections:
                                first_element = pair[0] if pair[0] not in old_ports_map else old_ports_map[pair[0]]
                                second_element = pair[1] if pair[1] not in old_ports_map else old_ports_map[pair[1]]
                                new_connections.append((first_element, second_element))
                            self.connections = new_connections
                            self.component_list.pop(index_list[0])
                            found = True
                        else:
                            raise ValueError("The number of ports do not match.")
                if not found:
                    raise ValueError("There is no such new signal component.")

    def list_played_components(self) -> list:
        played_ports = [port.replace('signal', '') for instance in self.component_list for port in instance.get_port_info() if 'signal' in port]
        adjacent_ports = []
        for element in played_ports:
            for tup in self.connections:
                if element in tup:
                    index = tup.index(element)
                    adjacent_ports.append(tup[1 - index])
                    break
        connections = []
        for element in adjacent_ports:
            element = '_'.join(element.split('_', 2)[:2])
            temp = []
            for tup in self.connections:
                p_list = [p for p in tup if element in p]
                if p_list:
                    index = tup.index(p_list[0])
                    temp.append(tup[1 - index])
            if len(temp) >= 2:
                connections.append(temp)
        played_components = []
        for connection in connections:
            played_couple = []
            for element in connection:
                name, id_str, _ = element.split('_', 2)
                id = int(id_str[2:])
                for component in self.component_list:
                    if component.name == name and component.id == id:
                        played_couple.append(component)
            played_components.append(played_couple)
        return played_components

    def list_all_played_component(self) -> list:
        played_dic = {}
        for subsys in self.subsystem_list:
            played_dic[f'subsystem_{subsys.subsystem_type}_{subsys.id}'] = subsys.list_played_components()
        played_dic['system'] = self.list_played_components()
        return played_dic

    def remove_after_last_underscore(self, s):
        last_underscore_index = s.rfind('_')
        if last_underscore_index != -1:
            return s[:last_underscore_index]
        return s

    def remove_substring_after_id(self, input_string):
        id_index = input_string.find('id')
        underscore_index = input_string.find('_', id_index)
        return input_string[:underscore_index]

    def find_paths(self, start, end):
        def path(visited, visited_nodes, current):
            if current == end:
                result.append(visited)
                return
            current_new = self.remove_substring_after_id(current)
            for pair in self.connections:
                new_pair = (self.remove_substring_after_id(pair[0]), self.remove_substring_after_id(pair[1]))
                if current_new in new_pair:
                    old_node = pair[0] if new_pair[0] == current_new else pair[1]
                    if old_node != end:
                        next_node = pair[0] if new_pair[1] == current_new else pair[1]
                        next_node_new = self.remove_substring_after_id(next_node)
                        if pair not in visited and next_node_new not in visited_nodes:
                            path(visited + [pair], visited_nodes | {next_node_new}, next_node)

        result = []
        path([], {start}, start)
        return result

    def extract_elements(self, elements, connections=None):
        if connections:
            connection_list = connections
        else:
            connection_list = self.connections
        result = [[] for _ in range(len(elements))]
        visited = set()
        def chain(start, index):
            visited.add(start)
            result[index].append(start)
            # for t in self.connections:
            for t in connection_list:
                if start in t:
                    next_node = t[0] if t[1] == start else t[1]
                    if next_node not in visited:
                        chain(next_node, index)
        for i, element in enumerate(elements):
            chain(element, i)
        return result

    def filter_connections(self, port_list):
        result = []
        for element in port_list:
            filter_connections = [t for t in self.connections if element in t]
            result.append(filter_connections)
        return result
