"""
SNMP Traps related intricacies
"""

### INCLUDES ###
import os
import copy

from py_knife.ordered_dict import OrderedDict

from ..database import DatabaseOrderedDict
from ..conversions import internal_name

from .common import SNMPMixin, SNMP_TRAP


### CONSTANTS ###
## Defaults ##
# SNMP Traps #
NEW_TRAP_DEFAULTS = {
    'name': '',
    'oid': '',
    'value': None
}

INPUT_1_TRAP = {
    'name': 'Digital Input 1 Trap',
    'oid': '1.3.6.1.4.1.38783.3.1.0',
    'value': '1'
}

INPUT_2_TRAP = {
    'name': 'Digital Input 2 Trap',
    'oid': '1.3.6.1.4.1.38783.3.2.0',
    'value': '1'
}

DEFAULT_TRAPS = OrderedDict()
DEFAULT_TRAPS[internal_name(INPUT_1_TRAP['name'])] = copy.deepcopy(INPUT_1_TRAP)
DEFAULT_TRAPS[internal_name(INPUT_2_TRAP['name'])] = copy.deepcopy(INPUT_2_TRAP)


### CLASSES ###
class SNMPTraps(DatabaseOrderedDict, SNMPMixin):
    def __init__(self):
        self.validation_string = SNMP_TRAP
        self.new_defaults = NEW_TRAP_DEFAULTS

        super(SNMPTraps, self).__init__(
            db_file=os.path.join('snmp', 'traps.db'),
            defaults=DEFAULT_TRAPS
        )
