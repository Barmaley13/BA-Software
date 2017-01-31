"""
Some Common Constants
"""

### INCLUDES ###
import os
import copy
import logging

from ..common import DATABASE_FOLDER


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

        field_key = address['index']
        LOGGER.debug('field_key: ' + str(field_key))

        validate = self.validation_string + NAME_FREE
        if not prospective_name:
            validate = self.validation_string + NAME_EMPTY
        else:
            field_name_taken = self.name_taken(field_key, prospective_name)
            if field_name_taken:
                validate = self.validation_string + NAME_TAKEN

        json_dict['form'] = validate
        json_dict['field_name_taken'] = int(field_name_taken)

        return json_dict

    def name_taken(self, field_key, prospective_name):
        """ Checks if SNMP Agent/Command name is taken already. Returns True or False """
        _name_taken = False

        for snmp_key, snmp_item in self.items():
            if field_key != snmp_key:
                if snmp_item['name'] == prospective_name:
                    _name_taken = True
                    break

        return _name_taken

    ## External(Web) Methods ##
    def get_by_key(self, snmp_key):
        """ Fetches particular SNMP Agent/Command/Trap """
        if snmp_key in self.keys():
            return self[snmp_key]
        else:
            return copy.deepcopy(self.new_defaults)
