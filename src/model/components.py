# -*- coding: utf-8 -*-

"""
The Component class has several subclasses, each representing a distinct category of components in Simulink, such as
sources, sensors, actuators, elements, mission, ports, signals, logic, utilities, and workspace.

Solution built upon code originally developed by Yu Zhang as part of a master thesis. Used with permission of
the Institute of Industrial Automation and Software Engineering (IAS) as part of the University of Stuttgart.
Source: https://github.com/yuzhang330/simulink-model-generation-and-evolution

Last modification: 28.11.2023
"""

__version__ = "2"
__author__ = "Patrick Hummel, Yu Zhang"

from abc import ABC, abstractmethod
from typing import Final, List, Type, Dict


class ComponentBlock(ABC):

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

    def __init__(self, parameters: Dict):
        self.id = -1
        self.ports = []

        if isinstance(parameters, type(None)):
            self.creation_parameters_dict = {}
        else:
            self.creation_parameters_dict = parameters

    @property
    @abstractmethod
    def parameter(self) -> dict:
        pass

    @property
    def name(self) -> str:
        return type(self).__name__

    @property
    def unique_name(self) -> str:
        return f"{self.name}_{self.id}"

    def as_dict(self) -> dict:
        return {"id": self.unique_name, "type": self.name, "parameters": self.parameter}

    def change_parameter(self, parameter_name: str, value):
        if hasattr(self, parameter_name):
            setattr(self, parameter_name, value)
        else:
            raise ValueError(f"{parameter_name} is not a valid parameter.")

    def list_attributes(self):
        return {attr: getattr(self, attr) for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")}

    def get_port_info(self) -> List[str]:

        port_info = []

        for port in self.ports:
            port_name = f"{self.__class__.__name__}_id{self.id}_port{port}"
            port_info.append(port_name)

        return port_info

    def take_port(self, string):
        ports = [port_item for port_item in self.get_port_info() if string in port_item]
        return ports


class LogicBlock(ComponentBlock, ABC):
    pass


# Logic
class ComparatorBlock(LogicBlock):

    DIRECTORY: Final[str] = "simulink/Quick Insert/Logic and Bit Operations/Equal"
    PORTS: Final[List[str]] = ['IN1', 'IN2', 'OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ComparatorBlock.counter
        ComparatorBlock.counter += 1
        
        # Start with default list of ports
        self.ports = ComparatorBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class VoterBlock(LogicBlock):

    DIRECTORY: Final[str] = "simulink/User-Defined Functions/MATLAB Function"
    PORTS: Final[List[str]] = ['IN1', 'OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VoterBlock.counter
        VoterBlock.counter += 1

        # Start with default list of ports
        self.ports = VoterBlock.PORTS

    @property
    def parameter(self) -> dict:

        function = """function y = voter(u)
                    u = u(~isnan(u));
                    y = mode(u);
                    end
                    """

        return {'Function': function}


class SparingBlock(LogicBlock):

    DIRECTORY: Final[str] = "simulink/User-Defined Functions/MATLAB Function"
    PORTS: Final[List[str]] = ['IN1', 'IN2', 'OUT1']
    counter: int = 0

    def __init__(self, n: int = 1, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SparingBlock.counter
        SparingBlock.counter += 1

        # Start with default list of ports
        self.ports = SparingBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.n = int(n)
        else:
            self.n = int(parameters["_n_count"])

    @property
    def parameter(self) -> dict:

        function = f"""function outputs = select(signals, error)

                    num = size(signals, 1);
                    selected = zeros({self.n}, size(signals, 2));

                    counter = 0;
                    for i = 1:num
                        if error(i) ~= 0 && counter < {self.n}
                            counter = counter + 1;
                            selected(counter, :) = signals(i, :);
                        end

                        if counter >= {self.n}
                            break;
                        end
                    end

                    outputs = selected; """

        return {'Function': function, "_n_count": self.n}


class SignalAlterBlock(LogicBlock):

    DIRECTORY: Final[str] = "simulink/User-Defined Functions/MATLAB Function"
    PORTS: Final[List[str]] = ['IN1', 'OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SignalAlterBlock.counter
        SignalAlterBlock.counter += 1

        # Start with default list of ports
        self.ports = SignalAlterBlock.PORTS

    @property
    def parameter(self) -> dict:

        function = """function y = alter(u)
                    y = u + 1;
                    end
                    """

        return {'Function': function}


# Workspace
class WorkspaceBlock(ComponentBlock, ABC):
    pass


class FromWorkspaceBlock(WorkspaceBlock):

    DIRECTORY: Final[str] = "simulink/Sources/From Workspace"
    PORTS: Final[List[str]] = ['OUT1']
    counter: int = 0

    def __init__(self, variable_name: str = 'simin', sample_time: int = 0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = FromWorkspaceBlock.counter
        FromWorkspaceBlock.counter += 1

        # Start with default list of ports
        self.ports = FromWorkspaceBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.variable_name = str(variable_name)
            self.sample_time = int(sample_time)
        else:
            self.variable_name = str(parameters["VariableName"])
            self.sample_time = int(parameters["SampleTime"])

    @property
    def parameter(self) -> dict:
        return {'SampleTime': self.sample_time, 'VariableName': self.variable_name}


class ToWorkspaceBlock(WorkspaceBlock):

    DIRECTORY: Final[str] = "simulink/Sinks/To Workspace"
    PORTS: Final[List[str]] = ['IN1']
    counter: int = 0

    def __init__(self, variable_name: str = 'simout', sample_time: int = -1, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ToWorkspaceBlock.counter
        ToWorkspaceBlock.counter += 1

        # Start with default list of ports
        self.ports = ToWorkspaceBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.variable_name = str(variable_name)
            self.sample_time = int(sample_time)
            self.save_format = 'Structure with Time'
        else:
            self.variable_name = str(parameters["VariableName"])
            self.sample_time = int(parameters["SampleTime"])
            self.save_format = str(parameters["SaveFormat"])

    @property
    def parameter(self) -> dict:
        return {'SampleTime': self.sample_time, 'VariableName': self.variable_name, 'SaveFormat': self.save_format}


# Port
class PortBlock(ComponentBlock, ABC):
    pass


class InportBlock(PortBlock):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/In1"
    PORTS: Final[List[str]] = ['IN1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = InportBlock.counter
        InportBlock.counter += 1

        # Start with default list of ports
        self.ports = InportBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class OutportBlock(PortBlock):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Out1"
    PORTS: Final[List[str]] = ['OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = OutportBlock.counter
        OutportBlock.counter += 1

        # Start with default list of ports
        self.ports = OutportBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class ConnectionPortBlock(PortBlock):

    DIRECTORY: Final[str] = "nesl_utility/Connection Port"
    PORTS: Final[List[str]] = ['RConn 1']
    counter: int = 0

    def __init__(self, direction: str = 'left', port_type: str = "Inport", parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ConnectionPortBlock.counter
        ConnectionPortBlock.counter += 1

        # Start with default list of ports
        self.ports = ConnectionPortBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.direction = str(direction)
            self.port_type = str(port_type)
        else:
            self.direction = str(parameters["Orientation"])
            self.port_type = str(parameters["_Port_Type"])

    @property
    def parameter(self) -> dict:
        return {'Orientation': self.direction, 'Side': self.direction, '_Port_Type': self.port_type}


# Utilities
class UtilitiesBlock(ComponentBlock, ABC):
    pass


class SolverBlock(UtilitiesBlock):

    DIRECTORY: Final[str] = "nesl_utility/Solver Configuration"
    PORTS: Final[List[str]] = ['RConn 1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SolverBlock.counter
        SolverBlock.counter += 1

        # Start with default list of ports
        self.ports = SolverBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class PSSimuConvBlock(UtilitiesBlock):

    DIRECTORY: Final[str] = "nesl_utility/PS-Simulink Converter"
    PORTS: Final[List[str]] = ['INLConn 1', 'OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = PSSimuConvBlock.counter
        PSSimuConvBlock.counter += 1

        # Start with default list of ports
        self.ports = PSSimuConvBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class SimuPSConvBlock(UtilitiesBlock):

    DIRECTORY: Final[str] = "nesl_utility/Simulink-PS Converter"
    PORTS: Final[List[str]] = ['IN1', 'OUTRConn 1']
    counter: int = 0

    def __init__(self, filter_str: str = 'filter', parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SimuPSConvBlock.counter
        SimuPSConvBlock.counter += 1

        # Start with default list of ports
        self.ports = SimuPSConvBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.filter_str = str(filter_str)
        else:
            self.filter_str = str(parameters["FilteringAndDerivatives"])

    @property
    def parameter(self) -> dict:
        return {'FilteringAndDerivatives': self.filter_str}


class ScopeBlock(UtilitiesBlock):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Scope"
    PORTS: Final[List[str]] = ['IN1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ScopeBlock.counter
        ScopeBlock.counter += 1

        # Start with default list of ports
        self.ports = ScopeBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class ReferenceBlock(UtilitiesBlock):

    DIRECTORY: Final[str] = "ee_lib/Connectors & References/Electrical Reference"
    PORTS: Final[List[str]] = ['LConn 1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ReferenceBlock.counter
        ReferenceBlock.counter += 1

        # Start with default list of ports
        self.ports = ReferenceBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class MuxBlock(UtilitiesBlock):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Mux"
    PORTS: Final[List[str]] = []
    counter: int = 0

    def __init__(self, num_input: int = 2, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = MuxBlock.counter
        MuxBlock.counter += 1

        # Start with default list of ports
        self.ports = MuxBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.num_input = int(num_input)
        else:
            self.num_input = int(parameters["Inputs"])

        for i in range(self.num_input):
            self.ports.append('IN' + str(i+1))

        self.ports.append('OUT1')

    def set_input(self, num_input):

        self.num_input = num_input
        self.ports.clear()

        for i in range(self.num_input):
            self.ports.append('IN' + str(i + 1))

        self.ports.append('OUT1')

    @property
    def parameter(self) -> dict:
        return {'Inputs': self.num_input}


class DemuxBlock(UtilitiesBlock):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Demux"
    PORTS: Final[List[str]] = ['IN1']
    counter: int = 0

    def __init__(self, num_output: int = 2, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = DemuxBlock.counter
        DemuxBlock.counter += 1

        # Start with default list of ports
        self.ports = DemuxBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.num_output = int(num_output)
        else:
            self.num_output = int(parameters["Outputs"])

        for i in range(self.num_output):
            self.ports.append('OUT' + str(i + 1))

    def set_output(self, num_output):

        self.num_output = num_output
        self.ports.clear()
        self.ports.append('IN1')

        for i in range(self.num_output):
            self.ports.append('OUT' + str(i + 1))

    @property
    def parameter(self) -> dict:
        return {'Outputs': self.num_output}


class VectorConcatenateBlock(UtilitiesBlock):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Vector Concatenate"
    PORTS: Final[List[str]] = []
    counter: int = 0

    def __init__(self, num_input: int = 2, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VectorConcatenateBlock.counter
        VectorConcatenateBlock.counter += 1

        # Start with default list of ports
        self.ports = VectorConcatenateBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.num_input = int(num_input)
        else:
            self.num_input = int(parameters["NumInputs"])

        for i in range(self.num_input):
            self.ports.append('IN' + str(i+1))

        self.ports.append('OUT1')

    def set_input(self, num_input):

        self.num_input = num_input
        self.ports.clear()

        for i in range(self.num_input):
            self.ports.append('IN' + str(i + 1))

        self.ports.append('OUT1')

    @property
    def parameter(self) -> dict:
        return {'NumInputs': self.num_input}


class CommonSwitchBlock(UtilitiesBlock):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Switch"
    PORTS: Final[List[str]] = ['IN1', 'IN2', 'IN3', 'OUT1']
    counter: int = 0

    def __init__(self, threshold: float = 0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CommonSwitchBlock.counter
        CommonSwitchBlock.counter += 1

        # Start with default list of ports
        self.ports = CommonSwitchBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.threshold = float(threshold)
        else:
            self.threshold = float(parameters["Threshold"])

    @property
    def parameter(self) -> dict:
        return {'Threshold': self.threshold}


class UnitDelayBlock(UtilitiesBlock):

    DIRECTORY: Final[str] = "simulink/Discrete/Unit Delay"
    PORTS: Final[List[str]] = ['IN1', 'OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = UnitDelayBlock.counter
        UnitDelayBlock.counter += 1

        # Start with default list of ports
        self.ports = UnitDelayBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


# Signal
class SignalBlock(ComponentBlock, ABC):
    pass


class ConstantBlock(SignalBlock):

    DIRECTORY: Final[str] = "simulink/Sources/Constant"
    PORTS: Final[List[str]] = ['OUT1']
    counter: int = 0

    def __init__(self, value: float = 1.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ConstantBlock.counter
        ConstantBlock.counter += 1

        # Start with default list of ports
        self.ports = ConstantBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.value = float(value)
        else:
            self.value = float(parameters["Value"])

    @property
    def parameter(self) -> dict:
        return {'Value': self.value}


class StepBlock(SignalBlock):

    DIRECTORY: Final[str] = "simulink/Sources/Step"
    PORTS: Final[List[str]] = ['OUT1']
    counter: int = 0

    def __init__(self, step_time: float = 1.0, initial_value: float = 0.0, final_value: float = 1.0, sample_time: float = 0.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = StepBlock.counter
        StepBlock.counter += 1

        # Start with default list of ports
        self.ports = StepBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.step_time = float(step_time)
            self.initial_value = float(initial_value)
            self.final_value = float(final_value)
            self.sample_time = float(sample_time)
        else:
            self.step_time = float(parameters["Time"])
            self.initial_value = float(parameters["Before"])
            self.final_value = float(parameters["After"])
            self.sample_time = float(parameters["SampleTime"])

    @property
    def parameter(self) -> dict:
        return {'Time': self.step_time, 'Before': self.initial_value, 'After': self.final_value, 'SampleTime': self.sample_time}


class SineBlock(SignalBlock):

    DIRECTORY: Final[str] = "simulink/Sources/Sine Wave"
    PORTS: Final[List[str]] = ['OUT1']
    counter: int = 0

    def __init__(self, amplitude: float = 1.0, bias: float = 0.0, frequency: float = 1.0, phase: float = 0.0, sample_time: float = 0.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SineBlock.counter
        SineBlock.counter += 1

        # Start with default list of ports
        self.ports = SineBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.amplitude = float(amplitude)
            self.bias = float(bias)
            self.frequency = float(frequency)
            self.phase = float(phase)
            self.sample_time = float(sample_time)
        else:
            self.amplitude = float(parameters["Amplitude"])
            self.bias = float(parameters["Bias"])
            self.frequency = float(parameters["Frequency"])
            self.phase = float(parameters["Phase"])
            self.sample_time = float(parameters["SampleTime"])

    @property
    def parameter(self) -> dict:
        return {'Amplitude': self.amplitude, 'Bias': self.bias, 'Frequency': self.frequency,
                'Phase': self.phase, 'SampleTime': self.sample_time}


# Actuator
class ActuatorBlock(ComponentBlock, ABC):
    pass


class ElectricalActuatorBlock(ActuatorBlock, ABC):
    pass


class CircuitBreakerBlock(ElectricalActuatorBlock):

    DIRECTORY: Final[str] = "ee_lib/Switches & Breakers/Circuit Breaker"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2', 'RConn 1']
    counter: int = 0

    def __init__(self, threshold: float = 0.5, breaker_behavior: int = 2, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CircuitBreakerBlock.counter
        CircuitBreakerBlock.counter += 1

        # Start with default list of ports
        self.ports = CircuitBreakerBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.threshold = float(threshold)
            self.breaker_behavior = int(breaker_behavior)
        else:
            self.threshold = float(parameters["threshold"])
            self.breaker_behavior = int(parameters["breaker_behavior"])

    @property
    def parameter(self) -> dict:
        return {'threshold': self.threshold, 'breaker_behavior': self.breaker_behavior}


class SPSTSwitchBlock(ElectricalActuatorBlock):

    DIRECTORY: Final[str] = "ee_lib/Switches & Breakers/SPST Switch"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2', 'RConn 1']
    counter: int = 0

    def __init__(self, threshold: float = 0.5, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SPSTSwitchBlock.counter
        SPSTSwitchBlock.counter += 1

        # Start with default list of ports
        self.ports = SPSTSwitchBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.threshold = float(threshold)
        else:
            self.threshold = float(parameters["Threshold"])

    @property
    def parameter(self) -> dict:
        return {'Threshold': self.threshold}


class SPDTSwitchBlock(ElectricalActuatorBlock):

    DIRECTORY: Final[str] = "ee_lib/Switches & Breakers/SPDT Switch"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2', 'RConn 1', 'RConn 2']
    counter: int = 0

    def __init__(self, threshold: float = 0.5, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SPDTSwitchBlock.counter
        SPDTSwitchBlock.counter += 1

        # Start with default list of ports
        self.ports = SPDTSwitchBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.threshold = float(threshold)
        else:
            self.threshold = float(parameters["Threshold"])

    @property
    def parameter(self) -> dict:
        return {'Threshold': self.threshold}


class SPMTSwitchBlock(ElectricalActuatorBlock):

    DIRECTORY: Final[str] = "ee_lib/Switches & Breakers/SPMT Switch"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2']
    counter: int = 0

    def __init__(self, number: int = 3, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SPMTSwitchBlock.counter
        SPMTSwitchBlock.counter += 1

        # Start with default list of ports
        self.ports = SPMTSwitchBlock.PORTS

        # Prefer values from parameters dictionary
        if not isinstance(parameters, type(None)):
            number = int(parameters["number_throws"])

        if number < 3:
            self.number = 3
        elif number > 8:
            self.number = 8
        else:
            self.number = number

        for i in range(self.number):
            self.ports.append('RConn' + ' ' + str(i+1))

    @property
    def parameter(self) -> dict:
        return {'number_throws': self.number}

    def change_throw_number(self, number):
        self.number = number
        self.ports = ['signalLConn 1', 'LConn 2']
        for i in range(self.number):
            self.ports.append('RConn' + ' ' + str(i+1))


# Sensor
class SensorBlock(ComponentBlock, ABC):
    pass


class ElectricalSensorBlock(SensorBlock, ABC):
    pass


class CurrentSensorBlock(ElectricalSensorBlock):

    DIRECTORY: Final[str] = "ee_lib/Sensors & Transducers/Current Sensor"
    PORTS: Final[List[str]] = ['scopeOUTRConn 1', '+LConn 1', '-RConn 2']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CurrentSensorBlock.counter
        CurrentSensorBlock.counter += 1

        # Start with default list of ports
        self.ports = CurrentSensorBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class VoltageSensorBlock(ElectricalSensorBlock):

    DIRECTORY: Final[str] = "ee_lib/Sensors & Transducers/Voltage Sensor"
    PORTS: Final[List[str]] = ['scopeOUTRConn 1', '+LConn 1', '-RConn 2']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VoltageSensorBlock.counter
        VoltageSensorBlock.counter += 1

        # Start with default list of ports
        self.ports = VoltageSensorBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


# Source
class SourceBlock(ComponentBlock, ABC):
    pass


class ElectricalSourceBlock(SourceBlock, ABC):
    pass


class BatteryBlock(ElectricalSourceBlock):

    DIRECTORY: Final[str] = "ee_lib/Sources/Battery"
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, vnom: float = 12, innerR: float = 2, capacity: float = 50, v_1: float = 11.5, ah_1: float = 25, infinite=None, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = BatteryBlock.counter
        BatteryBlock.counter += 1

        # Start with default list of ports
        self.ports = BatteryBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.vnom = float(vnom)
            self.innerR = float(innerR)
            self.capacity = float(capacity)
            self.v_1 = float(v_1)
            self.ah_1 = float(ah_1)
            self.infinite = infinite
        else:
            self.vnom = float(parameters["Vnom"])
            self.innerR = float(parameters["R1"])
            self.capacity = float(parameters["AH"])
            self.v_1 = float(parameters["V1"])
            self.ah_1 = float(parameters["AH1"])
            self.infinite = bool(parameters["Infinite"])

    @property
    def parameter(self) -> dict:

        if self.infinite:
            parameters = {'Vnom': self.vnom, 'R1': self.innerR}
        else:

            if self.v_1 > self.vnom:
                self.v_1 = self.vnom - 0.5
            if self.ah_1 / self.v_1 > self.capacity / self.vnom:
                self.ah_1 = self.v_1 * (self.capacity / self.vnom)

            parameters = {
                'prm_AH': '2',
                'Vnom': self.vnom,
                'R1': self.innerR,
                'AH': self.capacity,
                'V1': self.v_1,
                'AH1': self.ah_1
            }

        return parameters


class VoltageSourceACBlock(ElectricalSourceBlock):

    DIRECTORY: Final[str] = "ee_lib/Sources/Voltage Source"
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, peak: float = 10.0, phase_shift: float = 10.0, frequency: float = 50.0, dc_voltage: float = 0.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VoltageSourceACBlock.counter
        VoltageSourceACBlock.counter += 1

        # Start with default list of ports
        self.ports = VoltageSourceACBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.peak = float(peak)
            self.phase_shift = float(phase_shift)
            self.frequency = float(frequency)
            self.dc_voltage = float(dc_voltage)
        else:
            self.peak = float(parameters["ac_voltage"])
            self.phase_shift = float(parameters["ac_shift"])
            self.frequency = float(parameters["ac_frequency"])
            self.dc_voltage = float(parameters["dc_voltage"])

    @property
    def parameter(self) -> dict:
        return {'dc_voltage': self.dc_voltage, 'ac_voltage': self.peak,
                'ac_shift': self.phase_shift, 'ac_frequency': self.frequency}


class CurrentSourceACBlock(ElectricalSourceBlock):

    DIRECTORY: Final[str] = "ee_lib/Sources/Current Source"
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, peak: float = 10.0, phase_shift: float = 10.0, frequency: float = 50.0, dc_current: float = 0.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CurrentSourceACBlock.counter
        CurrentSourceACBlock.counter += 1

        # Start with default list of ports
        self.ports = CurrentSourceACBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.peak = float(peak)
            self.phase_shift = float(phase_shift)
            self.frequency = float(frequency)
            self.dc_current = float(dc_current)
        else:
            self.peak = float(parameters["ac_current"])
            self.phase_shift = float(parameters["ac_shift"])
            self.frequency = float(parameters["ac_frequency"])
            self.dc_current = float(parameters["dc_current"])

    @property
    def parameter(self) -> dict:
        return {'dc_current': self.dc_current, 'ac_current': self.peak,
                'ac_shift': self.phase_shift, 'ac_frequency': self.frequency}


class VoltageSourceDCBlock(ElectricalSourceBlock):

    DIRECTORY: Final[str] = "ee_lib/Sources/Voltage Source"
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, voltage: float = 10.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VoltageSourceDCBlock.counter
        VoltageSourceDCBlock.counter += 1

        # Start with default list of ports
        self.ports = VoltageSourceDCBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.voltage = float(voltage)
        else:
            self.voltage = float(parameters["dc_voltage"])

    @property
    def parameter(self) -> dict:
        return {'dc_voltage': self.voltage}


class ControlledVoltageSourceBlock(ElectricalSourceBlock):

    DIRECTORY: Final[str] = "fl_lib/Electrical/Electrical Sources/Controlled Voltage Source"
    PORTS: Final[List[str]] = ['signalINRConn 1', '+LConn 1', '-RConn 2']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ControlledVoltageSourceBlock.counter
        ControlledVoltageSourceBlock.counter += 1

        # Start with default list of ports
        self.ports = ControlledVoltageSourceBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class CurrentSourceDCBlock(ElectricalSourceBlock):

    DIRECTORY: Final[str] = "ee_lib/Sources/Current Source"
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, current: float = 10.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CurrentSourceDCBlock.counter
        CurrentSourceDCBlock.counter += 1

        # Start with default list of ports
        self.ports = CurrentSourceDCBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.current = float(current)
        else:
            self.current = float(parameters["dc_current"])

    @property
    def parameter(self) -> dict:
        return {'dc_current': self.current}


class ControlledCurrentSourceBlock(ElectricalSourceBlock):

    DIRECTORY: Final[str] = "fl_lib/Electrical/Electrical Sources/Controlled Current Source"
    PORTS: Final[List[str]] = ['signalINRConn 1', '+LConn 1', '-RConn 2']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ControlledCurrentSourceBlock.counter
        ControlledCurrentSourceBlock.counter += 1

        # Start with default list of ports
        self.ports = ControlledCurrentSourceBlock.PORTS

    @property
    def parameter(self) -> dict:
        return {}


# Element
class ElementBlock(ComponentBlock, ABC):
    pass


class ElectricalElementBlock(ElementBlock, ABC):
    pass


class CapacitorBlock(ElectricalElementBlock):

    DIRECTORY: Final[str] = "ee_lib/Passive/Capacitor"
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, capacitance: float = 10, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CapacitorBlock.counter
        CapacitorBlock.counter += 1

        # Start with default list of ports
        self.ports = CapacitorBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.capacitance = float(capacitance)
        else:
            self.capacitance = float(parameters["c"])

    @property
    def parameter(self):
        return {'c': self.capacitance}


class VariableCapacitorBlock(ElectricalElementBlock):

    DIRECTORY: Final[str] = "ee_lib/Passive/Variable Capacitor"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2', 'RConn 1']
    counter: int = 0

    def __init__(self, Cmin: float = 1e-9, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VariableCapacitorBlock.counter
        VariableCapacitorBlock.counter += 1

        # Start with default list of ports
        self.ports = VariableCapacitorBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.Cmin = float(Cmin)
        else:
            self.Cmin = float(parameters["Cmin"])

    @property
    def parameter(self):
        return {'Cmin': self.Cmin}


class InductorBlock(ElectricalElementBlock):

    DIRECTORY: Final[str] = "ee_lib/Passive/Inductor"
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, inductance: float = 10, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = InductorBlock.counter
        InductorBlock.counter += 1

        # Start with default list of ports
        self.ports = InductorBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.inductance = float(inductance)
        else:
            self.inductance = float(parameters["L"])

    @property
    def parameter(self) -> dict:
        return {'L': self.inductance}


class VariableInductorBlock(ElectricalElementBlock):

    DIRECTORY: Final[str] = "ee_lib/Passive/Variable Inductor"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2', 'RConn 1']
    counter: int = 0

    def __init__(self, Lmin: float = 1e-6, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VariableInductorBlock.counter
        VariableInductorBlock.counter += 1

        # Start with default list of ports
        self.ports = VariableInductorBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.Lmin = float(Lmin)
        else:
            self.Lmin = float(parameters["Lmin"])

    @property
    def parameter(self) -> dict:
        return {'Lmin': self.Lmin}


class ResistorBlock(ElectricalElementBlock):

    DIRECTORY: Final[str] = "ee_lib/Passive/Resistor"
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, resistance: float = 10.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ResistorBlock.counter
        ResistorBlock.counter += 1

        # Start with default list of ports
        self.ports = ResistorBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.resistance = float(resistance)
        else:
            self.resistance = float(parameters["R"])

    @property
    def parameter(self) -> dict:
        return {'R': self.resistance}


class VaristorBlock(ElectricalElementBlock):

    DIRECTORY: Final[str] = 'ee_lib/Passive/Varistor'
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, vclamp: float = 0.1, roff: float = 10.0, ron: float = 1.0, vln: float = 0.1, vnu: float = 100.0,
                 rLeak: float = 10.0, alphaNormal: float = 45.0, rUpturn: float = 0.1, prm: str = "linear", parameters: Dict = None):

        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VaristorBlock.counter
        VaristorBlock.counter += 1

        # Start with default list of ports
        self.ports = VaristorBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):

            if prm not in ['linear', 'power-law']:
                raise ValueError("The 'prm' must be either 'linear' or 'power-law'")

            self.prm = prm

            if self.prm == 'linear':
                self.vclamp = float(vclamp)
                self.roff = float(roff)
                self.ron = float(ron)

            elif self.prm == 'power-law':
                self.vln = float(vln)
                self.vnu = float(vnu)
                self.alphaNormal = float(alphaNormal)
                self.rUpturn = float(rUpturn)
                self.rLeak = float(rLeak)

        else:

            self.prm = parameters["prm"]

            if self.prm == 'linear' or self.prm == '1':
                self.prm = 'linear'
                self.vclamp = float(parameters["vclamp"])
                self.roff = float(parameters["roff"])
                self.ron = float(parameters["ron"])

            elif self.prm == 'power-law' or self.prm == '1':
                self.prm = 'power-law'
                self.vln = float(parameters["vln"])
                self.vnu = float(parameters["vnu"])
                self.alphaNormal = float(parameters["alphaNormal"])
                self.rUpturn = float(parameters["rUpturn"])
                self.rLeak = float(parameters["rLeak"])

    @property
    def parameter(self) -> dict:

        if self.prm == 'linear':
            parameters = {
                'prm': '1',
                'vclamp': self.vclamp,
                'roff': self.roff,
                'ron': self.ron
            }
        elif self.prm == 'power-law':
            if self.vln > self.vnu:
                self.vln = self.vnu - 50
            parameters = {
                'prm': '2',
                'vln': self.vln,
                'vnu': self.vnu,
                'alphaNormal': self.alphaNormal,
                'rUpturn': self.rUpturn,
                'rLeak': self.rLeak
            }
        else:
            print("Warning: prm should be 'linear' or 'power-law'")
            parameters = {}

        return parameters


class DiodeBlock(ElectricalElementBlock):

    DIRECTORY: Final[str] = 'ee_lib/Semiconductors & Converters/Diode'
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, forwardV: float = 0.5, onR: float = 0.01, breakV: float = 500, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = DiodeBlock.counter
        DiodeBlock.counter += 1

        # Start with default list of ports
        self.ports = DiodeBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.forwardV = float(forwardV)
            self.onR = float(onR)
            self.breakV = float(breakV)
        else:
            self.forwardV = float(parameters["Vf"])
            self.onR = float(parameters["Ron"])
            self.breakV = float(parameters["BV"])

    @property
    def parameter(self) -> dict:
        return {'Vf': self.forwardV, 'Ron': self.onR, 'BV': self.breakV}


# Mission
class MissionBlock(ComponentBlock, ABC):
    pass


class IncandescentLampBlock(MissionBlock):

    DIRECTORY: Final[str] = 'ee_lib/Passive/Incandescent Lamp'
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, r_0: float = 0.15, r_1: float = 1, Vrated: float = 12, alpha: float = 0.004, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = IncandescentLampBlock.counter
        IncandescentLampBlock.counter += 1

        # Start with default list of ports
        self.ports = IncandescentLampBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.r_0 = float(r_0)
            self.r_1 = float(r_1)
            self.Vrated = float(Vrated)
            self.alpha = float(alpha)
        else:
            self.r_0 = float(parameters["R0"])
            self.r_1 = float(parameters["R1"])
            self.Vrated = float(parameters["Vrated"])
            self.alpha = float(parameters["alpha"])

    @property
    def parameter(self) -> dict:
        return {'R0': self.r_0, 'R1': self.r_1, 'Vrated': self.Vrated, 'alpha': self.alpha}


class UniversalMotorBlock(MissionBlock):

    DIRECTORY: Final[str] = 'ee_lib/Electromechanical/Brushed Motors/Universal Motor'
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1', 'LConn 2', 'RConn 2']
    counter: int = 0

    def __init__(self, w_rated: float = 6500, P_rated: float = 75, V_dc: float = 200, P_in: float = 160, Ltot: float = 0.525, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = UniversalMotorBlock.counter
        UniversalMotorBlock.counter += 1

        # Start with default list of ports
        self.ports = UniversalMotorBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.w_rated = float(w_rated)
            self.P_rated = float(P_rated)
            self.V_dc = float(V_dc)
            self.P_in = float(P_in)
            self.Ltot = float(Ltot)
        else:
            self.w_rated = float(parameters["w_rated"])
            self.P_rated = float(parameters["P_rated"])
            self.V_dc = float(parameters["V_dc"])
            self.P_in = float(parameters["P_in"])
            self.Ltot = float(parameters["Ltot"])

    @property
    def parameter(self) -> dict:

        if self.P_in <= self.P_rated:
            self.P_in = self.P_rated + 50

        return {'w_rated': self.w_rated, 'P_rated': self.P_rated,
                'V_dc': self.V_dc, 'P_in': self.P_in, 'Ltot': self.Ltot}


class InertiaBlock(MissionBlock):

    DIRECTORY: Final[str] = 'fl_lib/Mechanical/Rotational Elements/Inertia'
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, inertia: float = 0.5, num_ports: int = 2, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = InertiaBlock.counter
        InertiaBlock.counter += 1

        # Start with default list of ports
        self.ports = InertiaBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.inertia = float(inertia)
            self.num_ports = str(num_ports)
        else:
            self.inertia = float(parameters['inertia'])
            self.num_ports = float(parameters['num_ports'])

    @property
    def parameter(self) -> dict:
        return {'inertia': self.inertia, 'num_ports': self.num_ports}


# Transistor
class TransistorBlock(ComponentBlock, ABC):
    pass


class NChannelMOSFETBlock(TransistorBlock):
    """
    N-Channel MOSFET Block

    :param r_ds: Drain-source on resistance R_DS(on) [Ohm]
    :type r_ds: float
    :param i_drain: Drain current, Ids, for R_DS(on) [A]
    :type i_drain: float
    :param v_gs: Gate-source voltage, Vgs, for R_DS(on) [V]
    :type v_gs: float
    :param v_th: Gate-source threshold voltage, Vth [V]
    :type v_th: float
    """

    DIRECTORY: Final[str] = 'ee_lib/Semiconductors & Converters/N-Channel MOSFET'
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1', 'RConn 2']     # -> RConn 1: Drain & RConn 2: Source
    counter: int = 0

    def __init__(self, r_ds: float = 0.025, i_drain: float = 6.0, v_gs: float = 10.0, v_th: float = 1.7, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = NChannelMOSFETBlock.counter
        NChannelMOSFETBlock.counter += 1

        # Start with default list of ports
        self.ports = NChannelMOSFETBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.r_ds = float(r_ds)
            self.i_drain = float(i_drain)
            self.v_gs = float(v_gs)
            self.v_th = float(v_th)
        else:
            self.r_ds = float(parameters['Rds'])
            self.i_drain = float(parameters['Id'])
            self.v_gs = float(parameters['Vgs'])
            self.v_th = float(parameters['Vth'])

    @property
    def parameter(self) -> dict:
        return {'Rds': self.r_ds, 'Id': self.i_drain, 'Vgs': self.v_gs, 'Vth': self.v_th}


class PChannelMOSFETBlock(TransistorBlock):
    """
    P-Channel MOSFET Block

    :param r_ds: Drain-source on resistance R_DS(on) [Ohm]
    :type r_ds: float
    :param i_drain: Drain current, Ids, for R_DS(on) [A]
    :type i_drain: float
    :param v_gs: Gate-source voltage, Vgs, for R_DS(on) [V]
    :type v_gs: float
    :param v_th: Gate-source threshold voltage, Vth [V]
    :type v_th: float
    """

    DIRECTORY: Final[str] = 'ee_lib/Semiconductors & Converters/P-Channel MOSFET'
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1', 'RConn 2']  # -> RConn 1: Source & RConn 2: Drain
    counter: int = 0

    def __init__(self, r_ds: float = 0.167, i_drain: float = -2.5, v_gs: float = -4.5, v_th: float = -1.4, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = PChannelMOSFETBlock.counter
        PChannelMOSFETBlock.counter += 1

        # Start with default list of ports
        self.ports = PChannelMOSFETBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.r_ds = float(r_ds)
            self.i_drain = float(i_drain)
            self.v_gs = float(v_gs)
            self.v_th = float(v_th)
        else:
            self.r_ds = float(parameters['Rds'])
            self.i_drain = float(parameters['Id'])
            self.v_gs = float(parameters['Vgs'])
            self.v_th = float(parameters['Vth'])

    @property
    def parameter(self) -> dict:
        return {'Rds': self.r_ds, 'Id': self.i_drain, 'Vgs': self.v_gs, 'Vth': self.v_th}


class NPNBipolarTransistorBlock(TransistorBlock):
    """
    NPN Bipolar Transistor Block

    :param h_fe: Forward current transfer ratio
    :type h_fe: float
    :param h_oe: Output admittance [1/Ohm]
    :type h_oe: float
    :param ic_h: Collector current at which h-parameters are defined [mA]
    :type ic_h: float
    :param vce_h: Collector-emitter voltage at which h-parameters are defined [V]
    :type vce_h: float
    :param vbe: Voltage Vbe [V]
    :type vbe: float
    :param i_vbe: Current Ib for voltage Vbe [mA]
    :type i_vbe: float
    :param br: Reverse current transfer ratio BR
    :type br: float
    :param r_c: Collector resistance RC [Ohm]
    :type r_c: float
    :param r_e: Emitter resistance RE [Ohm]
    :type r_e: float
    :param r_b: Emitter resistance RB [Ohm]
    :type r_b: float
    :param parameters: Block parameters in dictionary form.
    :type parameters: dict
    """

    DIRECTORY: Final[str] = 'ee_lib/Semiconductors & Converters/NPN Bipolar Transistor'
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1', 'RConn 2']     # -> LConn 1: Base RConn 1: Collector & RConn 2: Emitter
    counter: int = 0

    def __init__(self, h_fe: float = 100, h_oe: float = 50.0e-6, ic_h: float = 1.0, vce_h: float = 5.0,
                 vbe: float = 0.55, i_vbe: float = 0.5, br: float = 1.0,
                 r_c: float = 0.01, r_e: float = 1e-4, r_b: float = 1.0,
                 parameters: Dict = None):

        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = NPNBipolarTransistorBlock.counter
        NPNBipolarTransistorBlock.counter += 1

        # Start with default list of ports
        self.ports = NPNBipolarTransistorBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.h_fe = float(h_fe)
            self.h_oe = float(h_oe)
            self.ic_h = float(ic_h)
            self.vce_h = float(vce_h)
            self.vbe = float(vbe)
            self.i_vbe = float(i_vbe)
            self.br = float(br)
            self.r_c = float(r_c)
            self.r_e = float(r_e)
            self.r_b = float(r_b)

        else:
            self.h_fe = float(parameters['hfe'])
            self.h_oe = float(parameters['hoe'])
            self.ic_h = float(parameters['Ic_h'])
            self.vce_h = float(parameters['Vce_h'])
            self.vbe = float(parameters['V1'])
            self.i_vbe = float(parameters['I1'])
            self.br = float(parameters['BR'])
            self.r_c = float(parameters['RC'])
            self.r_e = float(parameters['RE'])
            self.r_b = float(parameters['RB'])

    @property
    def parameter(self) -> dict:
        return {'hfe': self.h_fe, 'hoe': self.h_oe, 'Ic_h': self.ic_h, 'Vce_h': self.vce_h,
                'V1': self.vbe, 'I1': self.i_vbe, 'BR': self.br, 'RC': self.r_c, 'RE': self.r_e, 'RB': self.r_b}


class PNPBipolarTransistorBlock(TransistorBlock):
    """
    PNP Bipolar Transistor Block

    :param h_fe: Forward current transfer ratio
    :type h_fe: float
    :param h_oe: Output admittance [1/Ohm]
    :type h_oe: float
    :param ic_h: Collector current at which h-parameters are defined [mA]
    :type ic_h: float
    :param vce_h: Collector-emitter voltage at which h-parameters are defined [V]
    :type vce_h: float
    :param vbe: Voltage Vbe [V]
    :type vbe: float
    :param i_vbe: Current Ib for voltage Vbe [mA]
    :type i_vbe: float
    :param br: Reverse current transfer ratio BR
    :type br: float
    :param r_c: Collector resistance RC [Ohm]
    :type r_c: float
    :param r_e: Emitter resistance RE [Ohm]
    :type r_e: float
    :param r_b: Emitter resistance RB [Ohm]
    :type r_b: float
    :param parameters: Block parameters in dictionary form.
    :type parameters: dict
    """

    DIRECTORY: Final[str] = 'ee_lib/Semiconductors & Converters/PNP Bipolar Transistor'
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1', 'RConn 2']  # -> LConn 1: Base RConn 1: Emitter & RConn 2: Collector
    counter: int = 0

    def __init__(self, h_fe: float = 100, h_oe: float = 50.0e-6, ic_h: float = -1.0, vce_h: float = -5.0,
                 vbe: float = -0.55, i_vbe: float = -0.5, br: float = 1.0,
                 r_c: float = 0.01, r_e: float = 1e-4, r_b: float = 1.0,
                 parameters: Dict = None):

        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = PNPBipolarTransistorBlock.counter
        PNPBipolarTransistorBlock.counter += 1

        # Start with default list of ports
        self.ports = PNPBipolarTransistorBlock.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.h_fe = float(h_fe)
            self.h_oe = float(h_oe)
            self.ic_h = float(ic_h)
            self.vce_h = float(vce_h)
            self.vbe = float(vbe)
            self.i_vbe = float(i_vbe)
            self.br = float(br)
            self.r_c = float(r_c)
            self.r_e = float(r_e)
            self.r_b = float(r_b)

        else:
            self.h_fe = float(parameters['hfe'])
            self.h_oe = float(parameters['hoe'])
            self.ic_h = float(parameters['Ic_h'])
            self.vce_h = float(parameters['Vce_h'])
            self.vbe = float(parameters['V1'])
            self.i_vbe = float(parameters['I1'])
            self.br = float(parameters['BR'])
            self.r_c = float(parameters['RC'])
            self.r_e = float(parameters['RE'])
            self.r_b = float(parameters['RB'])

    @property
    def parameter(self) -> dict:
        return {'hfe': self.h_fe, 'hoe': self.h_oe, 'Ic_h': self.ic_h, 'Vce_h': self.vce_h,
                'V1': self.vbe, 'I1': self.i_vbe, 'BR': self.br, 'RC': self.r_c, 'RE': self.r_e, 'RB': self.r_b}
