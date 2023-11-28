# -*- coding: utf-8 -*-

"""
The Interface serves as a bridge between Python and MATLAB Simulink and translate python models into Simscape models.

Solution built upon code originally developed by Yu Zhang as part of a master thesis. Used with permission of
the Institute of Industrial Automation and Software Engineering (IAS) as part of the University of Stuttgart.
Source: https://github.com/yuzhang330/simulink-model-generation-and-evolution

Last modification: 28.11.2023
"""

__version__ = "2"
__author__ = "Patrick Hummel, Yu Zhang"

import matlab
import matlab.engine

from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod

from config.gobal_constants import PATH_DEFAULT_SIMSCAPE_MODEL_OUTPUT_SLX
from src.model.components import FromWorkspaceBlock
from src.model.system import System, Connection, Subsystem


class SimulinkInterface(ABC):

    @abstractmethod
    def input_systemparameters(self):
        pass

    @abstractmethod
    def input_connections(self, eng, connection, path, type):
        pass

    @abstractmethod
    def input_subsystem(self, eng, model_name, subsystem, position):
        pass

    @abstractmethod
    def input_components(self, eng, model_name, component, position):
        pass


class SystemSimulinkAdapter(SimulinkInterface):

    def input_systemparameters(self):
        pass

    def __init__(self, system):
        self.system = system

    def make_positions(self, input_list):

        sub_lists = []
        start_index = 0
        odd_count = 1

        while start_index < len(input_list):
            end_index = start_index + odd_count
            sub_list = input_list[start_index:end_index]
            sub_lists.append(sub_list)
            start_index = end_index
            odd_count += 2

        new_input_list = []

        for index, sublist in enumerate(sub_lists):

            for subindex, position in enumerate(sublist):
                new_position = [element + 100 * index for element in position]

                if subindex % 2 == 0:
                    new_position[0] = new_position[0] - (subindex // 2) * 100
                    new_position[2] = new_position[0] + 30
                else:
                    new_position[1] = new_position[1] - ((subindex + 1) // 2) * 100
                    new_position[3] = new_position[1] + 30

                new_input_list.append(new_position)

        return new_input_list

    def process_string(self, input_string):

        input_string = input_string.replace('id', '')
        parts = input_string.split('port')
        part_1 = parts[0].rsplit('_', 1)[0]
        part_2 = parts[1]

        return part_1, part_2

    def port_sort(self, item):
        if 'OUT' in item:
            return 0
        elif 'IN' in item:
            return 2
        else:
            return 1

    def input_components(self, eng, model_name, component, position):

        eng.add_block(component.__class__.DIRECTORY, f'{model_name}/{component.name}_{component.id}', nargout=0)

        position_matlab = matlab.double(position)
        eng.set_param(f'{model_name}/{component.name}_{component.id}', 'Position', position_matlab, nargout=0)

        for param_name, param_value in component.parameter.items():
            param_value_str = str(param_value) if not isinstance(param_value, str) else param_value
            eng.set_param(f'{model_name}/{component.name}_{component.id}', param_name, param_value_str,
                          nargout=0)

    def input_connections(self, eng, connection: Connection, path, type):

        if type == 'subsystem':

            block_1, port_1 = self.process_string(connection.from_port)

            if isinstance(connection.from_block, Subsystem):
                handle = eng.get_param(f'{path}/{connection.from_port_path()}', 'PortHandles')
                handle = handle['RConn'] - 1

            else:
                handle = eng.get_param(f'{path}/{block_1}', 'PortHandles')
                s = port_1.split(' ')
                if isinstance(handle[s[0]], float):
                    handle = handle[s[0]]
                else:
                    handle = handle[s[0]][0][int(s[1])-1]

            block_2, port_2 = self.process_string(connection.to_port)

            if 'subsystem' in block_2:
                handle_1 = eng.get_param(f'{path}/{block_2}/{port_2}', 'PortHandles')
                handle_1 = handle_1['RConn'] - 1
            else:
                handle_1 = eng.get_param(f'{path}/{block_2}', 'PortHandles')
                s = port_2.split(' ')

                if isinstance(handle_1[s[0]], float):
                    handle_1 = handle_1[s[0]]
                else:
                    handle_1 = handle_1[s[0]][0][int(s[1])-1]

            eng.add_line(path, handle, handle_1, 'autorouting', 'on', nargout=0)

    def input_subsystem(self, eng, model_name, subsystem, position):

        # Add a subsystem to the Simulink model
        subsystem_path = f'{model_name}/{subsystem.unique_name}'

        eng.add_block('simulink/Ports & Subsystems/Subsystem', subsystem_path, nargout=0)

        position_matlab = matlab.double(position)
        eng.set_param(f'{subsystem_path}', 'Position', position_matlab, nargout=0)
        eng.delete_line(subsystem_path, 'In1/1', 'Out1/1', nargout=0)
        eng.delete_block(f'{subsystem_path}/In1', nargout=0)
        eng.delete_block(f'{subsystem_path}/Out1', nargout=0)

        positions = [[100, 100, 130, 130]] * len(subsystem.component_list)
        positions = self.make_positions(positions)

        for index, component in enumerate(subsystem.component_list):

            eng.add_block(component.__class__.DIRECTORY, f'{subsystem_path}/{component.unique_name}', nargout=0)
            position_matlab = matlab.double(positions[index])

            eng.set_param(f'{subsystem_path}/{component.unique_name}', 'Position', position_matlab, nargout=0)

            for param_name, param_value in component.parameter.items():

                if param_name == 'Function':
                    fcn_name = eng.get_param(f'{subsystem_path}/{component.unique_name}', 'MATLABFunctionConfiguration')
                    eng.setfield(fcn_name, 'FunctionScript', param_value, nargout=0)
                else:
                    param_value_str = str(param_value) if not isinstance(param_value, str) else param_value

                    # Ignore parameters that start with underscore (not intended for MATLAB Simulink)
                    if not param_name.startswith("_"):
                        eng.set_param(f'{subsystem_path}/{component.unique_name}',
                                      param_name, param_value_str, nargout=0)

            if isinstance(component, FromWorkspaceBlock):

                time_values = matlab.double([0])
                data_values = matlab.double([[1]])

                my_signal = {
                    'time': time_values,
                    'signals': {
                        'values': data_values
                    }
                }

                eng.workspace[component.variable_name] = eng.struct(my_signal)
                # eng.set_param(f'{subsystem_path}/{component.name}_{component.id}', 'VariableName',
                #               component.variable_name, nargout=0)

        for connection in subsystem.connection_list:
            eng.add_line(subsystem_path, connection.from_port_path(), connection.to_port_path(), 'autorouting', 'on', nargout=0)

    def input_system_parameters(self, eng, model_name):

        for param_name, param_value in self.system.parameter.items():
            param_value_str = str(param_value) if not isinstance(param_value, str) else param_value

            # Ignore parameters that start with underscore (not intended for MATLAB Simulink)
            if not param_name.startswith("_"):
                eng.set_param(model_name, param_name, param_value_str, nargout=0)

    def input_system(self, eng, model_name):

        self.input_system_parameters(eng, model_name)

        positions = [[100, 100, 130, 130]] * (len(self.system.subsystem_list) + len(self.system.component_list))
        positions = self.make_positions(positions)

        for index, subsys in enumerate(self.system.subsystem_list):
            self.input_subsystem(eng, model_name, subsys, positions[index])

        for index, component in enumerate(self.system.component_list):
            self.input_components(eng, model_name, component, positions[index + len(self.system.subsystem_list)])

        for connection in self.system.connection_list:

            if isinstance(connection.from_block, Subsystem):
                handle_from = eng.get_param(f'{model_name}/{connection.from_port_path()}', 'PortHandles')['RConn'] - 1
            else:
                handle_from = eng.get_param(f'{model_name}/{connection.from_block.unique_name}', 'PortHandles')
                s = connection.from_port.split(' ')
                port_name = s[0]
                port_nr = s[1]

                # In case there is more than one port
                if isinstance(handle_from[port_name], float):
                    handle_from = handle_from[port_name]
                else:
                    handle_from = handle_from[port_name][0][int(port_nr) - 1]

            if isinstance(connection.to_block, Subsystem):
                handle_to = eng.get_param(f'{model_name}/{connection.to_port_path()}', 'PortHandles')['RConn'] - 1
            else:
                handle_to = eng.get_param(f'{model_name}/{connection.to_block.unique_name}', 'PortHandles')
                s = connection.to_port.split(' ')
                port_name = s[0]
                port_nr = s[1]

                # In case there is more than one port
                if isinstance(handle_to[port_name], float):
                    handle_to = handle_to[port_name]
                else:
                    handle_to = handle_to[port_name][0][int(port_nr) - 1]

            eng.add_line(model_name, handle_from, handle_to, 'autorouting', 'on', nargout=0)

    def change_parameter(self, eng, model_name, parameter_name, parameter_value, component_name, component_id,
                         subsystem_type=None, subsystem_id=None):

        param_value_str = str(parameter_value) if not isinstance(parameter_value, str) else parameter_value

        # Ignore parameters that start with underscore (not intended for MATLAB Simulink)
        if parameter_name.startswith("_"):
            return

        if subsystem_type and subsystem_id is not None:
            eng.set_param(f'{model_name}/subsystem_{subsystem_id}/{component_name}_{component_id}',
                          parameter_name, param_value_str, nargout=0)
        else:
            eng.set_param(f'{model_name}/{component_name}_{component_id}', parameter_name, param_value_str, nargout=0)


class Implementer:

    def __init__(self, adapter):
        self.eng = None
        self.adapter = adapter

    def input_to_simulink(self, system: System, simulink_model_name: str):

        if not isinstance(self.eng, type(None)):
            self.eng.quit()

        interf = self.adapter(system)

        self.eng = matlab.engine.start_matlab()
        self.eng.new_system(simulink_model_name, nargout=0)
        self.eng.open_system(simulink_model_name, nargout=0)

        interf.input_system(self.eng, simulink_model_name)

    def save_to_disk(self, simulink_model_name: str, output_directory: Path = None):

        if not isinstance(self.eng, type(None)):

            if isinstance(output_directory, type(None)):
                output_directory = PATH_DEFAULT_SIMSCAPE_MODEL_OUTPUT_SLX

            # Include current date in filename
            datetime_now = datetime.now()
            datetime_now_str = datetime_now.strftime("%Y%m%d_%H%M")

            output_filepath = output_directory / f"simscape_{simulink_model_name}_{datetime_now_str}.slx"

            self.eng.save_system(simulink_model_name, str(output_filepath))

    def read_parameter(self, model_name, parameter_name, component_name, component_id,
                       subsystem_type=None, subsystem_id=None):

        # Ignore parameters that start with underscore (not intended for MATLAB Simulink)
        if parameter_name.startswith("_"):
            return 0

        if subsystem_type and subsystem_id is not None:
            values = self.eng.get_param(f'{model_name}/subsystem_{subsystem_id}/{component_name}_{component_id}',
                                        parameter_name, nargout=1)
        else:
            values = self.eng.get_param(f'{model_name}/{component_name}_{component_id}', parameter_name, nargout=1)

        return values

    def change_parameter(self, model_name, parameter_name, parameter_value, component_name, component_id,
                         subsystem_type=None, subsystem_id=None):

        # Ignore parameters that start with underscore (not intended for MATLAB Simulink)
        if parameter_name.startswith("_"):
            return

        param_value_str = str(parameter_value) if not isinstance(parameter_value, str) else parameter_value

        if subsystem_type and subsystem_id is not None:
            self.eng.set_param(f'{model_name}/subsystem_{subsystem_id}/{component_name}_{component_id}',
                          parameter_name, param_value_str, nargout=0)
        else:
            self.eng.set_param(f'{model_name}/{component_name}_{component_id}', parameter_name, param_value_str, nargout=0)

    def change_variable(self, variable_name, variable_value):

        if isinstance(variable_value, dict):
            self.eng.workspace[variable_name] = self.eng.struct(variable_value)
        else:
            self.eng.workspace[variable_name] = variable_value

    def change_component_control_variable(self, sys, variable_value, component_name, component_id, subsystem_type=None, subsystem_id=None):

        variable_name = ''

        if subsystem_type is not None and subsystem_id is not None:
            subsys = f'subsystem_{subsystem_id}'
        else:
            subsys = 'system'

        full_list = sys.list_all_played_component()
        sub_list = full_list[subsys]

        for pair in sub_list:
            if pair[0].name == component_name and pair[0].id == component_id:
                variable_name = pair[1].variable_name

        if variable_name == '':
            raise ValueError('There is no such controlled component')
        else:
            if isinstance(variable_value, dict):
                self.eng.workspace[variable_name] = self.eng.struct(variable_value)
            else:
                self.eng.workspace[variable_name] = variable_value

    def read_variable(self, variable_name, simulation_out=True):
        if simulation_out:
            value = self.eng.eval(f'out.get("{variable_name}")')
        else:
            value = self.eng.workspace[variable_name]
        return value

    def input_systemparameters(self):
        pass
