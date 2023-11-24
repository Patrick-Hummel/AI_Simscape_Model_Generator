# -*- coding: utf-8 -*-

"""
The Component class has several subclasses, each representing a distinct category of components in Simulink, such as
sources, sensors, actuators, elements, mission, ports, signals, logic, utilities, and workspace.

Solution built upon code originally developed by Yu Zhang as part of a master thesis. Used with permission of
the Institute of Industrial Automation and Software Engineering (IAS) as part of the University of Stuttgart.
Source: https://github.com/yuzhang330/simulink-model-generation-and-evolution

Last modification: 23.11.2023
"""

__version__ = "2"
__author__ = "Patrick Hummel, Yu Zhang"

from abc import ABC, abstractmethod
from typing import Final, List, Type, Dict


class Component(ABC):

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


class Logic(Component, ABC):
    pass


# Logic
class Comparator(Logic):

    DIRECTORY: Final[str] = "simulink/Quick Insert/Logic and Bit Operations/Equal"
    PORTS: Final[List[str]] = ['IN1', 'IN2', 'OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Comparator.counter
        Comparator.counter += 1
        
        # Start with default list of ports
        self.ports = Comparator.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class Voter(Logic):

    DIRECTORY: Final[str] = "simulink/User-Defined Functions/MATLAB Function"
    PORTS: Final[List[str]] = ['IN1', 'OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Voter.counter
        Voter.counter += 1

        # Start with default list of ports
        self.ports = Voter.PORTS

    @property
    def parameter(self) -> dict:

        function = """function y = voter(u)
                    u = u(~isnan(u));
                    y = mode(u);
                    end
                    """

        return {'Function': function}


class Sparing(Logic):

    DIRECTORY: Final[str] = "simulink/User-Defined Functions/MATLAB Function"
    PORTS: Final[List[str]] = ['IN1', 'IN2', 'OUT1']
    counter: int = 0

    def __init__(self, n: int = 1, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Sparing.counter
        Sparing.counter += 1

        # Start with default list of ports
        self.ports = Sparing.PORTS

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


class SignalAlter(Logic):

    DIRECTORY: Final[str] = "simulink/User-Defined Functions/MATLAB Function"
    PORTS: Final[List[str]] = ['IN1', 'OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SignalAlter.counter
        SignalAlter.counter += 1

        # Start with default list of ports
        self.ports = SignalAlter.PORTS

    @property
    def parameter(self) -> dict:

        function = """function y = alter(u)
                    y = u + 1;
                    end
                    """

        return {'Function': function}


# Workspace
class Workspace(Component, ABC):
    pass


class FromWorkspace(Workspace):

    DIRECTORY: Final[str] = "simulink/Sources/From Workspace"
    PORTS: Final[List[str]] = ['OUT1']
    counter: int = 0

    def __init__(self, variable_name: str = 'simin', sample_time: int = 0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = FromWorkspace.counter
        FromWorkspace.counter += 1

        # Start with default list of ports
        self.ports = FromWorkspace.PORTS

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


class ToWorkspace(Workspace):

    DIRECTORY: Final[str] = "simulink/Sinks/To Workspace"
    PORTS: Final[List[str]] = ['IN1']
    counter: int = 0

    def __init__(self, variable_name: str = 'simout', sample_time: int = -1, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ToWorkspace.counter
        ToWorkspace.counter += 1

        # Start with default list of ports
        self.ports = ToWorkspace.PORTS

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
class Port(Component, ABC):
    pass


class Inport(Port):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/In1"
    PORTS: Final[List[str]] = ['IN1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Inport.counter
        Inport.counter += 1

        # Start with default list of ports
        self.ports = Inport.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class Outport(Port):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Out1"
    PORTS: Final[List[str]] = ['OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Outport.counter
        Outport.counter += 1

        # Start with default list of ports
        self.ports = Outport.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class ConnectionPort(Port):

    DIRECTORY: Final[str] = "nesl_utility/Connection Port"
    PORTS: Final[List[str]] = ['RConn 1']
    counter: int = 0

    def __init__(self, direction: str = 'left', port_type: str = "Inport", parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ConnectionPort.counter
        ConnectionPort.counter += 1

        # Start with default list of ports
        self.ports = ConnectionPort.PORTS

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
class Utilities(Component, ABC):
    pass


class Solver(Utilities):

    DIRECTORY: Final[str] = "nesl_utility/Solver Configuration"
    PORTS: Final[List[str]] = ['RConn 1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Solver.counter
        Solver.counter += 1

        # Start with default list of ports
        self.ports = Solver.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class PSSimuConv(Utilities):

    DIRECTORY: Final[str] = "nesl_utility/PS-Simulink Converter"
    PORTS: Final[List[str]] = ['INLConn 1', 'OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = PSSimuConv.counter
        PSSimuConv.counter += 1

        # Start with default list of ports
        self.ports = PSSimuConv.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class SimuPSConv(Utilities):

    DIRECTORY: Final[str] = "nesl_utility/Simulink-PS Converter"
    PORTS: Final[List[str]] = ['IN1', 'OUTRConn 1']
    counter: int = 0

    def __init__(self, filter_str: str = 'filter', parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SimuPSConv.counter
        SimuPSConv.counter += 1

        # Start with default list of ports
        self.ports = SimuPSConv.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.filter_str = str(filter_str)
        else:
            self.filter_str = str(parameters["FilteringAndDerivatives"])

    @property
    def parameter(self) -> dict:
        return {'FilteringAndDerivatives': self.filter_str}


class Scope(Utilities):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Scope"
    PORTS: Final[List[str]] = ['IN1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Scope.counter
        Scope.counter += 1

        # Start with default list of ports
        self.ports = Scope.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class Reference(Utilities):

    DIRECTORY: Final[str] = "ee_lib/Connectors & References/Electrical Reference"
    PORTS: Final[List[str]] = ['LConn 1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Reference.counter
        Reference.counter += 1

        # Start with default list of ports
        self.ports = Reference.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class Mux(Utilities):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Mux"
    PORTS: Final[List[str]] = []
    counter: int = 0

    def __init__(self, num_input: int = 2, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Mux.counter
        Mux.counter += 1

        # Start with default list of ports
        self.ports = Mux.PORTS

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


class Demux(Utilities):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Demux"
    PORTS: Final[List[str]] = ['IN1']
    counter: int = 0

    def __init__(self, num_output: int = 2, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Demux.counter
        Demux.counter += 1

        # Start with default list of ports
        self.ports = Demux.PORTS

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


class VectorConcatenate(Utilities):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Vector Concatenate"
    PORTS: Final[List[str]] = []
    counter: int = 0

    def __init__(self, num_input: int = 2, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VectorConcatenate.counter
        VectorConcatenate.counter += 1

        # Start with default list of ports
        self.ports = VectorConcatenate.PORTS

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


class CommonSwitch(Utilities):

    DIRECTORY: Final[str] = "simulink/Commonly Used Blocks/Switch"
    PORTS: Final[List[str]] = ['IN1', 'IN2', 'IN3', 'OUT1']
    counter: int = 0

    def __init__(self, threshold: float = 0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CommonSwitch.counter
        CommonSwitch.counter += 1

        # Start with default list of ports
        self.ports = CommonSwitch.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.threshold = float(threshold)
        else:
            self.threshold = float(parameters["Threshold"])

    @property
    def parameter(self) -> dict:
        return {'Threshold': self.threshold}


class UnitDelay(Utilities):

    DIRECTORY: Final[str] = "simulink/Discrete/Unit Delay"
    PORTS: Final[List[str]] = ['IN1', 'OUT1']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = UnitDelay.counter
        UnitDelay.counter += 1

        # Start with default list of ports
        self.ports = UnitDelay.PORTS

    @property
    def parameter(self) -> dict:
        return {}


# Signal
class Signal(Component, ABC):
    pass


class Constant(Signal):

    DIRECTORY: Final[str] = "simulink/Sources/Constant"
    PORTS: Final[List[str]] = ['OUT1']
    counter: int = 0

    def __init__(self, value: float = 1.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Constant.counter
        Constant.counter += 1

        # Start with default list of ports
        self.ports = Constant.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.value = float(value)
        else:
            self.value = float(parameters["Value"])

    @property
    def parameter(self) -> dict:
        return {'Value': self.value}


class Step(Signal):

    DIRECTORY: Final[str] = "simulink/Sources/Step"
    PORTS: Final[List[str]] = ['OUT1']
    counter: int = 0

    def __init__(self, step_time: float = 1.0, initial_value: float = 0.0, final_value: float = 1.0, sample_time: float = 0.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Step.counter
        Step.counter += 1

        # Start with default list of ports
        self.ports = Step.PORTS

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


class Sine(Signal):

    DIRECTORY: Final[str] = "simulink/Sources/Sine Wave"
    PORTS: Final[List[str]] = ['OUT1']
    counter: int = 0

    def __init__(self, amplitude: float = 1.0, bias: float = 0.0, frequency: float = 1.0, phase: float = 0.0, sample_time: float = 0.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Sine.counter
        Sine.counter += 1

        # Start with default list of ports
        self.ports = Sine.PORTS

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
class Actuator(Component, ABC):
    pass


class ElectricalActuator(Actuator, ABC):
    pass


class CircuitBreaker(ElectricalActuator):

    DIRECTORY: Final[str] = "ee_lib/Switches & Breakers/Circuit Breaker"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2', 'RConn 1']
    counter: int = 0

    def __init__(self, threshold: float = 0.5, breaker_behavior: int = 2, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CircuitBreaker.counter
        CircuitBreaker.counter += 1

        # Start with default list of ports
        self.ports = CircuitBreaker.PORTS

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


class SPSTSwitch(ElectricalActuator):

    DIRECTORY: Final[str] = "ee_lib/Switches & Breakers/SPST Switch"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2', 'RConn 1']
    counter: int = 0

    def __init__(self, threshold: float = 0.5, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SPSTSwitch.counter
        SPSTSwitch.counter += 1

        # Start with default list of ports
        self.ports = SPSTSwitch.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.threshold = float(threshold)
        else:
            self.threshold = float(parameters["Threshold"])

    @property
    def parameter(self) -> dict:
        return {'Threshold': self.threshold}


class SPDTSwitch(ElectricalActuator):

    DIRECTORY: Final[str] = "ee_lib/Switches & Breakers/SPDT Switch"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2', 'RConn 1', 'RConn 2']
    counter: int = 0

    def __init__(self, threshold: float = 0.5, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SPDTSwitch.counter
        SPDTSwitch.counter += 1

        # Start with default list of ports
        self.ports = SPDTSwitch.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.threshold = float(threshold)
        else:
            self.threshold = float(parameters["Threshold"])

    @property
    def parameter(self) -> dict:
        return {'Threshold': self.threshold}


class SPMTSwitch(ElectricalActuator):

    DIRECTORY: Final[str] = "ee_lib/Switches & Breakers/SPMT Switch"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2']
    counter: int = 0

    def __init__(self, number: int = 3, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = SPMTSwitch.counter
        SPMTSwitch.counter += 1

        # Start with default list of ports
        self.ports = SPMTSwitch.PORTS

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
class Sensor(Component, ABC):
    pass


class ElectricalSensor(Sensor, ABC):
    pass


class CurrentSensor(ElectricalSensor):

    DIRECTORY: Final[str] = "ee_lib/Sensors & Transducers/Current Sensor"
    PORTS: Final[List[str]] = ['scopeOUTRConn 1', '+LConn 1', '-RConn 2']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CurrentSensor.counter
        CurrentSensor.counter += 1

        # Start with default list of ports
        self.ports = CurrentSensor.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class VoltageSensor(ElectricalSensor):

    DIRECTORY: Final[str] = "ee_lib/Sensors & Transducers/Voltage Sensor"
    PORTS: Final[List[str]] = ['scopeOUTRConn 1', '+LConn 1', '-RConn 2']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VoltageSensor.counter
        VoltageSensor.counter += 1

        # Start with default list of ports
        self.ports = VoltageSensor.PORTS

    @property
    def parameter(self) -> dict:
        return {}


# Source
class Source(Component, ABC):
    pass


class ElectricalSource(Source, ABC):
    pass


class Battery(ElectricalSource):

    DIRECTORY: Final[str] = "ee_lib/Sources/Battery"
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, vnom: float = 12, innerR: float = 2, capacity: float = 50, v_1: float = 11.5, ah_1: float = 25, infinite=None, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Battery.counter
        Battery.counter += 1

        # Start with default list of ports
        self.ports = Battery.PORTS

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


class VoltageSourceAC(ElectricalSource):

    DIRECTORY: Final[str] = "ee_lib/Sources/Voltage Source"
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, peak: float = 10.0, phase_shift: float = 10.0, frequency: float = 50.0, dc_voltage: float = 0.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VoltageSourceAC.counter
        VoltageSourceAC.counter += 1

        # Start with default list of ports
        self.ports = VoltageSourceAC.PORTS

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


class CurrentSourceAC(ElectricalSource):

    DIRECTORY: Final[str] = "ee_lib/Sources/Current Source"
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, peak: float = 10.0, phase_shift: float = 10.0, frequency: float = 50.0, dc_current: float = 0.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CurrentSourceAC.counter
        CurrentSourceAC.counter += 1

        # Start with default list of ports
        self.ports = CurrentSourceAC.PORTS

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


class VoltageSourceDC(ElectricalSource):

    DIRECTORY: Final[str] = "ee_lib/Sources/Voltage Source"
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, voltage: float = 10.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VoltageSourceDC.counter
        VoltageSourceDC.counter += 1

        # Start with default list of ports
        self.ports = VoltageSourceDC.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.voltage = float(voltage)
        else:
            self.voltage = float(parameters["dc_voltage"])

    @property
    def parameter(self) -> dict:
        return {'dc_voltage': self.voltage}


class ControlledVoltageSource(ElectricalSource):

    DIRECTORY: Final[str] = "fl_lib/Electrical/Electrical Sources/Controlled Voltage Source"
    PORTS: Final[List[str]] = ['signalINRConn 1', '+LConn 1', '-RConn 2']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ControlledVoltageSource.counter
        ControlledVoltageSource.counter += 1

        # Start with default list of ports
        self.ports = ControlledVoltageSource.PORTS

    @property
    def parameter(self) -> dict:
        return {}


class CurrentSourceDC(ElectricalSource):

    DIRECTORY: Final[str] = "ee_lib/Sources/Current Source"
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, current: float = 10.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = CurrentSourceDC.counter
        CurrentSourceDC.counter += 1

        # Start with default list of ports
        self.ports = CurrentSourceDC.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.current = float(current)
        else:
            self.current = float(parameters["dc_current"])

    @property
    def parameter(self) -> dict:
        return {'dc_current': self.current}


class ControlledCurrentSource(ElectricalSource):

    DIRECTORY: Final[str] = "fl_lib/Electrical/Electrical Sources/Controlled Current Source"
    PORTS: Final[List[str]] = ['signalINRConn 1', '+LConn 1', '-RConn 2']
    counter: int = 0

    def __init__(self, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = ControlledCurrentSource.counter
        ControlledCurrentSource.counter += 1

        # Start with default list of ports
        self.ports = ControlledCurrentSource.PORTS

    @property
    def parameter(self) -> dict:
        return {}


# Element
class Element(Component, ABC):
    pass


class ElectricalElement(Element, ABC):
    pass


class Capacitor(ElectricalElement):

    DIRECTORY: Final[str] = "ee_lib/Passive/Capacitor"
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, capacitance: float = 10, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Capacitor.counter
        Capacitor.counter += 1

        # Start with default list of ports
        self.ports = Capacitor.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.capacitance = float(capacitance)
        else:
            self.capacitance = float(parameters["c"])

    @property
    def parameter(self):
        return {'c': self.capacitance}


class VariableCapacitor(ElectricalElement):

    DIRECTORY: Final[str] = "ee_lib/Passive/Variable Capacitor"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2', 'RConn 1']
    counter: int = 0

    def __init__(self, Cmin: float = 1e-9, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VariableCapacitor.counter
        VariableCapacitor.counter += 1

        # Start with default list of ports
        self.ports = VariableCapacitor.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.Cmin = float(Cmin)
        else:
            self.Cmin = float(parameters["Cmin"])

    @property
    def parameter(self):
        return {'Cmin': self.Cmin}


class Inductor(ElectricalElement):

    DIRECTORY: Final[str] = "ee_lib/Passive/Inductor"
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, inductance: float = 10, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Inductor.counter
        Inductor.counter += 1

        # Start with default list of ports
        self.ports = Inductor.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.inductance = float(inductance)
        else:
            self.inductance = float(parameters["L"])

    @property
    def parameter(self) -> dict:
        return {'L': self.inductance}


class VariableInductor(ElectricalElement):

    DIRECTORY: Final[str] = "ee_lib/Passive/Variable Inductor"
    PORTS: Final[List[str]] = ['signalINLConn 1', 'LConn 2', 'RConn 1']
    counter: int = 0

    def __init__(self, Lmin: float = 1e-6, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = VariableInductor.counter
        VariableInductor.counter += 1

        # Start with default list of ports
        self.ports = VariableInductor.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.Lmin = float(Lmin)
        else:
            self.Lmin = float(parameters["Lmin"])

    @property
    def parameter(self) -> dict:
        return {'Lmin': self.Lmin}


class Resistor(ElectricalElement):

    DIRECTORY: Final[str] = "ee_lib/Passive/Resistor"
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, resistance: float = 10.0, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Resistor.counter
        Resistor.counter += 1

        # Start with default list of ports
        self.ports = Resistor.PORTS

        # Prefer values from parameters dictionary
        if isinstance(parameters, type(None)):
            self.resistance = float(resistance)
        else:
            self.resistance = float(parameters["R"])

    @property
    def parameter(self) -> dict:
        return {'R': self.resistance}


class Varistor(ElectricalElement):

    DIRECTORY: Final[str] = 'ee_lib/Passive/Varistor'
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, vclamp: float = 0.1, roff: float = 10.0, ron: float = 1.0, vln: float = 0.1, vnu: float = 100.0,
                 rLeak: float = 10.0, alphaNormal: float = 45.0, rUpturn: float = 0.1, prm: str = "linear", parameters: Dict = None):

        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Varistor.counter
        Varistor.counter += 1

        # Start with default list of ports
        self.ports = Varistor.PORTS

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


class Diode(ElectricalElement):

    DIRECTORY: Final[str] = 'ee_lib/Semiconductors & Converters/Diode'
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, forwardV: float = 0.5, onR: float = 0.01, breakV: float = 500, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Diode.counter
        Diode.counter += 1

        # Start with default list of ports
        self.ports = Diode.PORTS

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
class Mission(Component, ABC):
    pass


class IncandescentLamp(Mission):

    DIRECTORY: Final[str] = 'ee_lib/Passive/Incandescent Lamp'
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1']
    counter: int = 0

    def __init__(self, r_0: float = 0.15, r_1: float = 1, Vrated: float = 12, alpha: float = 0.004, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = IncandescentLamp.counter
        IncandescentLamp.counter += 1

        # Start with default list of ports
        self.ports = IncandescentLamp.PORTS

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


class UniversalMotor(Mission):

    DIRECTORY: Final[str] = 'ee_lib/Electromechanical/Brushed Motors/Universal Motor'
    PORTS: Final[List[str]] = ['+LConn 1', '-RConn 1', 'LConn 2', 'RConn 2']
    counter: int = 0

    def __init__(self, w_rated: float = 6500, P_rated: float = 75, V_dc: float = 200, P_in: float = 160, Ltot: float = 0.525, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = UniversalMotor.counter
        UniversalMotor.counter += 1

        # Start with default list of ports
        self.ports = UniversalMotor.PORTS

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


class Inertia(Mission):

    DIRECTORY: Final[str] = 'fl_lib/Mechanical/Rotational Elements/Inertia'
    PORTS: Final[List[str]] = ['LConn 1', 'RConn 1']
    counter: int = 0

    def __init__(self, inertia: float = 0.5, num_ports: int = 2, parameters: Dict = None):
        super().__init__(parameters)

        # Each instance gets a unique ID
        self.id = Inertia.counter
        Inertia.counter += 1

        # Start with default list of ports
        self.ports = Inertia.PORTS

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
