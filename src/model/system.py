# -*- coding: utf-8 -*-

"""
This module contains the Container, System, Subsystem and Connection classes.

Solution built upon code originally developed by Yu Zhang as part of a master thesis. Used with permission of
the Institute of Industrial Automation and Software Engineering (IAS) as part of the University of Stuttgart.
Source: https://github.com/yuzhang330/simulink-model-generation-and-evolution

Last modification: 23.11.2023
"""

__version__ = "2"
__author__ = "Patrick Hummel, Yu Zhang"

import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict

from config.gobal_constants import MATLAB_DEFAULT_SOLVER, MATLAB_DEFAULT_STOP_TIME, PATH_DEFAULT_SYSTEM_OUTPUT_JSON
from src.model.components import Component, Signal, Port, Resistor, Varistor, Diode, Inductor, VariableInductor, \
    Capacitor, VariableCapacitor


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

    def __init__(self, name: str, in_ports: List[Port] = None, out_ports: List[Port] = None,
                 component_list: List[Component] = None, connection_list: List[Connection] = None):

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

            if isinstance(component, Component):

                if isinstance(component, Port):
                    self.in_ports.append(component)

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
        return [f"{component.name}_id{component.ID}" for component in self.component_list]

    def list_connections(self):
        return [f"{connection.from_port} -> {connection.to_port}" for connection in self.connection_list]


class Subsystem(Container):

    counter: int = 0

    def __init__(self, name: str = "NewSubsystem", in_ports: List[Port] = None, out_ports: List[Port] = None,
                 component_list: List[Component] = None, connection_list: List[Connection] = None):

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

            implemented_component_types_dict = Component.get_implemented_component_types_dict()

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
            for cls in Signal.__subclasses__():
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


class System(Container):
    def __init__(self, name: str = "NewSystem", in_ports: List[Port] = None, out_ports: List[Port] = None,
                 component_list: List[Component] = None, connection_list: List[Connection] = None,
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

            implemented_component_types_dict = Component.get_implemented_component_types_dict()

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

    def list_subsystem(self) -> list:
        return [f"{subsystem.name}_id{subsystem.id}" for subsystem in self.subsystem_list]

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
                for cls in Signal.__subclasses__():
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
