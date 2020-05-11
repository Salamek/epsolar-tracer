# -*- coding: iso-8859-15 -*-

# import the server implementation
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.mei_message import *
from epsolar_tracer.registers import registerByName, registers, coils
from epsolar_tracer.enums.CoilTypeEnum import CoilTypeEnum
from epsolar_tracer.enums.RegisterTypeEnum import RegisterTypeEnum
from typing import Union


# ---------------------------------------------------------------------------#
# Logging
# ---------------------------------------------------------------------------#
import logging

_logger = logging.getLogger(__name__)


class EPsolarTracerClient:
    """ EPsolar Tracer client
    """

    def __init__(self, serialclient: ModbusClient=None, **kwargs):
        """ Initialize a serial client instance
        """
        self.unit = kwargs.get('unit', 1)
        if serialclient is None:
            port = kwargs.get('port', '/dev/ttyXRUSB0')
            baudrate = kwargs.get('baudrate', 115200)
            self.client = ModbusClient(method='rtu', port=port, baudrate=baudrate, kwargs=kwargs)
        else:
            self.client = serialclient

    def connect(self):
        """ Connect to the serial
        :returns: True if connection succeeded, False otherwise
        """
        try:
            return self.client.connect()
        except AttributeError:
            # !FIXME there is bug in pymodbus when rtu mode is used and connection is not made:
            # !FIXME AttributeError: 'NoneType' object has no attribute 'interCharTimeout' that simply means connection failed
            return False

    def close(self):
        """ Closes the underlying connection
        """
        return self.client.close()

    def read_device_info(self):
        request = ReadDeviceInformationRequest(unit=self.unit)
        response = self.client.execute(request)
        return response

    def read_input(self, register_type: Union[RegisterTypeEnum, CoilTypeEnum]):
        if type(register_type) == 'str':
            register = registerByName(register_type)
        elif type(register_type) == RegisterTypeEnum:
            register = registers.get(register_type)
        elif type(register_type) == CoilTypeEnum:
            register = coils.get(register_type)

        if not register:
            raise Exception("Unknown register {}".format(register_type.name))

        if register.is_coil():
            response = self.client.read_coils(register.address, register.size, unit=self.unit)
        elif register.is_discrete_input():
            response = self.client.read_discrete_inputs(register.address, register.size, unit=self.unit)
        elif register.is_input_register():
            response = self.client.read_input_registers(register.address, register.size, unit=self.unit)
        else:
            response = self.client.read_holding_registers(register.address, register.size, unit=self.unit)
        return register.decode(response)

    def write_output(self, register_type: Union[RegisterTypeEnum, CoilTypeEnum], value):
        if type(register_type) == 'str':
            register = registerByName(register_type)
        elif type(register_type) == RegisterTypeEnum:
            register = registers.get(register_type)
        elif type(register_type) == CoilTypeEnum:
            register = coils.get(register_type)

        if not register:
            raise Exception("Unknown register {}".format(register_type.name))

        values = register.encode(value)
        response = False
        if register.is_coil():
            self.client.write_coil(register.address, values, unit=self.unit)
            response = True
        elif register.is_discrete_input():
            _logger.error("Cannot write discrete input {}".format(register_type.name))
            pass
        elif register.is_input_register():
            _logger.error("Cannot write input register {}".format(register_type.name))
            pass
        else:
            self.client.write_registers(register.address, values, unit=self.unit)
            response = True
        return response


__all__ = [
    "EPsolarTracerClient",
]
