"""
SNMP Commands related intricacies
"""

### INCLUDES ###
import os
import copy

from py_knife.ordered_dict import OrderedDict

from ..database import DatabaseOrderedDict
from ..conversions import internal_name


### CONSTANTS ###
## Strings ##
SNMP_COMMAND = '*SNMP Command'

## Defaults ##
# SNMP Commands #
NEW_COMMAND_DEFAULTS = {
    'name': '',
    'type': 'get',
    'oid': '',
    'value_type': 'None',
    'value': None
}
SNMP_AGENT_DESCRIPTION = {
    'name': 'SNMP Agent Description',
    'type': 'get',
    'oid': '1.3.6.1.2.1.1.1.0',
    'value_type': 'None',
    'value': None
}

RELAY_1_ON = {
    'name': 'Relay 1 On',
    'type': 'set',
    'oid': '1.3.6.1.4.1.38783.3.3.0',
    'value_type': 'integer',
    'value': 1
}

RELAY_1_OFF = {
    'name': 'Relay 1 Off',
    'type': 'set',
    'oid': '1.3.6.1.4.1.38783.3.3.0',
    'value_type': 'integer',
    'value': 0
}

RELAY_2_ON = {
    'name': 'Relay 2 On',
    'type': 'set',
    'oid': '1.3.6.1.4.1.38783.3.5.0',
    'value_type': 'integer',
    'value': 1
}

RELAY_2_OFF = {
    'name': 'Relay 2 Off',
    'type': 'set',
    'oid': '1.3.6.1.4.1.38783.3.5.0',
    'value_type': 'integer',
    'value': 0
}

DEFAULT_COMMANDS = OrderedDict()
DEFAULT_COMMANDS[internal_name(SNMP_AGENT_DESCRIPTION['name'])] = copy.deepcopy(SNMP_AGENT_DESCRIPTION)
DEFAULT_COMMANDS[internal_name(RELAY_1_ON['name'])] = copy.deepcopy(RELAY_1_ON)
DEFAULT_COMMANDS[internal_name(RELAY_1_OFF['name'])] = copy.deepcopy(RELAY_1_OFF)
DEFAULT_COMMANDS[internal_name(RELAY_2_ON['name'])] = copy.deepcopy(RELAY_2_ON)
DEFAULT_COMMANDS[internal_name(RELAY_2_OFF['name'])] = copy.deepcopy(RELAY_2_OFF)


### CLASSES ###
class SNMPCommands(DatabaseOrderedDict):
    def __init__(self):
        super(SNMPCommands, self).__init__(
            db_file=os.path.join('snmp', 'commands.db'),
            defaults=DEFAULT_COMMANDS
        )

        # Name validation and default SNMP Command value
        self.validation_string = SNMP_COMMAND
        self._default_value = NEW_COMMAND_DEFAULTS
