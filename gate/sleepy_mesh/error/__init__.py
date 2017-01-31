"""
Error Related Intricacies
Shared by Modbus Server and Sleepy Mesh Network
"""

### INCLUDES ###
import copy
import logging

from py_knife.ordered_dict import OrderedDict

from gate.strings import FIELD_UNIT

from base import BaseError, DEFAULT_ERROR_DATA_TYPES, DEFAULT_ERROR_REGISTERS, generate_default_error_dict
from snmp import SnmpError, DEFAULT_SNMP_ERROR_DATA_TYPES, DEFAULT_SNMP_DICT
from modbus import ModbusError


### CONSTANTS ###
## Error Codes & Error Messages ##
DEFAULT_NODE_ERROR_REGISTERS = {
    'generic': None,
    'node_fault': None
}

# TODO: Get rid of this dependency!
default_error_data_types = copy.deepcopy(DEFAULT_ERROR_DATA_TYPES)
default_snmp_error_data_types = copy.deepcopy(DEFAULT_SNMP_ERROR_DATA_TYPES)
default_error_data_types.update(default_snmp_error_data_types)

default_error_registers = copy.deepcopy(DEFAULT_ERROR_REGISTERS)
default_node_error_registers = copy.deepcopy(DEFAULT_NODE_ERROR_REGISTERS)
default_error_registers.update(default_node_error_registers)

DEFAULT_ERROR_DICT = generate_default_error_dict(default_error_data_types, default_error_registers)

# Generic Error Codes #
HW_ERROR = 0
ABSENT_NODE = 1
OLD_FIRMWARE = 2
OLD_SOFTWARE = 3
OLD_SOFTWARE_DETECTED = 4

# Generic Error Messages #
GENERIC_MESSAGES = {
    HW_ERROR: ' experiencing hardware error!',
    ABSENT_NODE: ' is not present on the network!',
    OLD_FIRMWARE: ' firmware is out of date! Please upgrade firmware!',
    OLD_SOFTWARE: ' software is out of date! Please upgrade software!',
    OLD_SOFTWARE_DETECTED: ' detected obsolete network packet! Some of the field units may require software upgrade!',
}

# NODE ERROR CODES (!!!HAVE TO MATCH NODE&BASE CODE ERROR CODES!!!)#
# Satellite Modem Errors
SM_PREAMBLE = 0
SM_LENGTH = 1
SM_CRC = 2
SM_UNKNOWN = 3
# ADC Data Mismatch
ADC_MISMATCH = 7            # This fault is detected at gate level
# ADC Errors
ADC_EOC = 8                 # This fault is detected at gate level
ADC_EXR = 9                 # This fault is detected at gate level
ADC_SIG = 10                # This fault is detected at gate level
# ADC and PCF Overflow
ADC_OVERFLOW = 11
PCF_OVERFLOW = 12
# Hardware Errors
XTAL_FAILURE = 13
SPI_FAILURE = 14

# Node Error Messages  #
NODE_MESSAGES = OrderedDict()
NODE_MESSAGES[SPI_FAILURE] = "SPI does not function properly! Make sure node on the latest firmware!"
NODE_MESSAGES[XTAL_FAILURE] = "RTC oscillator does not function properly!"
NODE_MESSAGES[PCF_OVERFLOW] = "Countdown timer mode or period overflow"
NODE_MESSAGES[ADC_OVERFLOW] = "No such ADC Channel!"
NODE_MESSAGES[ADC_SIG] = "Received sign indicator ADC error"
NODE_MESSAGES[ADC_EXR] = "Received extended input range ADC error"
NODE_MESSAGES[ADC_EOC] = "Received end of conversion ADC error"
NODE_MESSAGES[ADC_MISMATCH] = "ADC Data mismatch error!"
NODE_MESSAGES[SM_UNKNOWN] = "Unknown satellite modem response!"
NODE_MESSAGES[SM_CRC] = "Bad CRC satellite modem error!"
NODE_MESSAGES[SM_LENGTH] = "Packet length mismatch satellite modem error!"
NODE_MESSAGES[SM_PREAMBLE] = "Preamble mismatch satellite modem error!"

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def set_error_args(node, error_field, error_code, error_message=None):
    """ Overloading set_error to automatically generate error_messages for the nodes """
    error_code = int(error_code)
    if error_message is None:
        error_message_dict = {'node_fault': NODE_MESSAGES, 'generic': GENERIC_MESSAGES}
        _error_message = error_message_dict[error_field][error_code]
        if error_field == 'node_fault':
            error_message = _error_message
        elif error_field == 'generic':
            error_message = FIELD_UNIT + " '" + str(node['name']) + "'" + _error_message

    return error_field, error_code, error_message


### CLASSES ###
class NodeError(SnmpError, ModbusError):
    """ Methods related to Node Error Engine """
    def __init__(self, **kwargs):
        kwargs['auto_load'] = False

        super(NodeError, self).__init__(**kwargs)

        self._default_error_registers.update(DEFAULT_NODE_ERROR_REGISTERS)

        self.load()
