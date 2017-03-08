"""
Some Common Constants
"""

### INCLUDES ###
import os
import copy
import logging

from ..common import DATABASE_FOLDER
from ..conversions import internal_name

### CONSTANTS ###
## SNMP Responses ##
SNMP_RESPONSES_PATH = os.path.join(DATABASE_FOLDER, 'snmp', '_commands.db')
TRAPS_FILE = os.path.join('snmp', '_traps.db')

## Strings ##
SNMP_AGENT = '*SNMP Agent'
SNMP_COMMAND = '*SNMP Command'
SNMP_TRAP = '*SNMP Trap'
NAME_FREE = ' name is available'
NAME_EMPTY = ' name can not be empty!'
NAME_TAKEN = ' name is taken already!'

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
# FIXME: Fix warnings in this class
class SNMPMixin(object):
    def validation(self, address, prospective_name):
        """ Validates prospective SNMP Agent/Command Name """
        json_dict = {}
        field_name_taken = False

        validate = NAME_FREE
        if not prospective_name:
            validate = NAME_EMPTY
        else:
            field_name_taken = self.name_taken(address, prospective_name)
            if field_name_taken:
                validate = NAME_TAKEN

        json_dict['form'] = self.validation_string + validate
        json_dict['field_name_taken'] = int(field_name_taken)

        return json_dict

    def name_taken(self, field_key, prospective_name):
        """ Checks if SNMP Agent/Command name is taken already. Returns True or False """
        output = False

        for snmp_key, snmp_item in self.items():
            if field_key != snmp_key:
                if internal_name(snmp_item['name']) == internal_name(prospective_name):
                    output = True
                    break

        return output

    ## External(Web) Methods ##
    def get_by_key(self, snmp_key):
        """ Fetches particular SNMP Agent/Command/Trap """
        if snmp_key in self.keys():
            return self[snmp_key]
        else:
            return copy.deepcopy(self.new_defaults)
