"""
SNMP Error Mixin
"""

### INCLUDES ###
import copy
import logging

from py_knife.decorators import simple_decorator

from base import BaseError, LENGTH


### CONSTANTS ###
## Default SNMP Dictionary ##
# Working with lists and indexes just to test code!!!
DEFAULT_SNMP_DICT = {'agent': None, 'set': None, 'clear': None, 'trap': None}
DEFAULT_SNMP_ERROR_DATA_TYPES = {'_snmp': [copy.deepcopy(DEFAULT_SNMP_DICT)] * LENGTH}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
# SNMP Error Decorator #
@simple_decorator
def match_snmp_args(func):
    """ Decorator that matches SNMP Agent and SNMP Command """
    def _match_snmp_args(*args, **kwargs):
        self, snmp_agent, snmp_clear_command = args
        kwargs['send_command'] = True
        kwargs['break'] = False

        for error_field in self['error']['_snmp'].keys():
            kwargs['error_field'] = error_field
            for error_code in range(len(self['error']['_snmp'][error_field])):
                kwargs['error_code'] = error_code
                error_mask = 1 << error_code
                kwargs['error_mask'] = error_mask
                error_register = self['error']['_alarms'][error_field]
                if error_register & error_mask:
                    snmp_dict = self.get_snmp(error_field, error_code)
                    kwargs['snmp_dict'] = snmp_dict
                    if snmp_dict['agent'] == snmp_agent:
                        kwargs = func(*args, **kwargs)

                        if kwargs['break']:
                            break

            if not kwargs['send_command']:
                if 'snmp_type' in kwargs and kwargs['snmp_type'] == 'clear':
                    break

        return kwargs['send_command']

    return _match_snmp_args


### CLASSES ###
class SnmpError(BaseError):
    def __init__(self, **kwargs):
        super(SnmpError, self).__init__(**kwargs)
        self._default_error_data_types.update(DEFAULT_SNMP_ERROR_DATA_TYPES)

    ## Public Methods ##
    @match_snmp_args
    def check_snmp_trap_ack(self, snmp_agent, snmp_clear_command, **kwargs):
        """ Trigger _change_error_ack by incoming SNMP trap """
        kwargs['snmp_type'] = 'trap'

        if kwargs['snmp_dict']['trap'] == snmp_clear_command:
            # Clear during operation triggered by SNMP Trap
            self._change_error_ack(kwargs['error_field'], kwargs['error_code'], False)

        return kwargs

    @match_snmp_args
    def check_snmp_clear_ack(self, snmp_agent, snmp_clear_command, **kwargs):
        """ Checks if send Clear SNMP Command condition exists """
        kwargs['snmp_type'] = 'clear'

        if kwargs['snmp_dict']['clear'] == snmp_clear_command:
            # Perform check during operation triggered by ack
            ack_register = self['error']['_acks'][kwargs['error_field']]
            kwargs['send_command'] &= bool((ack_register & kwargs['error_mask']) == 0)

            if not kwargs['send_command']:
                kwargs['break'] = True

        return kwargs

    def get_snmp(self, error_field, error_code):
        """ Returns particular set of snmp alarms/acks """
        error_code = int(error_code)
        return self['error']['_snmp'][error_field][error_code]

    def set_snmp(self, error_field, error_code, input_snmp_dict):
        """ Sets particular set of snmp alarms/acks """
        error_code = int(error_code)
        snmp_dict = copy.deepcopy(DEFAULT_SNMP_DICT)
        snmp_dict.update(input_snmp_dict)
        self['error']['_snmp'][error_field][error_code] = snmp_dict

    def update_snmp_dict(self, snmp_type, old_snmp_key, new_snmp_key):
        """ Updates all snmp dictionaries with new key value """
        snmp_types = {
            'agent': ('agent', ),
            'command': ('set', 'clear'),
            'trap': ('trap',)
        }

        if snmp_type in snmp_types:
            for error_field in self['error']['_snmp'].keys():
                for error_code in range(len(self['error']['_snmp'][error_field])):
                    snmp_dict = self.get_snmp(error_field, error_code)
                    for _snmp_type in snmp_types[snmp_type]:
                        if snmp_dict[_snmp_type] == old_snmp_key:
                            snmp_dict[_snmp_type] = new_snmp_key

                    self.set_snmp(error_field, error_code, snmp_dict)

    # Made strictly for overloading! #
    def send_snmp(self, *args, **kwargs):
        """ Sends Set(or Clear) SNMP Command """
        # self._manager.snmp_server.send_snmp(*args, **kwargs)
        raise NotImplementedError

    def clear_snmp(self, *args, **kwargs):
        """ Clears SNMP Command """
        # self._manager.snmp_server.clear_snmp(*args, **kwargs)
        raise NotImplementedError

    ## Private Methods ##
    # Downstream #
    def _set_error_ack(self, error_field, error_code, ack_value):
        """ Set Error Ack """
        super(SnmpError, self)._set_error_ack(error_field, error_code, ack_value)
        self.__set_snmp_ack(error_field, error_code)

    def _clear_error_ack(self, error_field, error_code, ack_value):
        """ Clear Error Ack """
        super(SnmpError, self)._clear_error_ack(error_field, error_code, ack_value)
        self.__clear_snmp_ack(error_field, error_code)

    ## Class-Private Methods ##
    def __set_snmp_ack(self, error_field, error_code):
        """ Checks if particular snmp command needs to be sent out """
        if self._system_settings.snmp_enable:
            # Figure out if Send SNMP Command condition exists
            snmp_agent = self['error']['_snmp'][error_field][error_code]['agent']
            if snmp_agent is not None:
                snmp_set_command = self['error']['_snmp'][error_field][error_code]['set']
                if snmp_set_command is not None:
                    LOGGER.debug("Sending Set SNMP Command")
                    LOGGER.debug("error_field: " + str(error_field) + " error_code: " + str(error_code))

                    self.send_snmp(snmp_agent, snmp_set_command)

    def __clear_snmp_ack(self, error_field, error_code):
        """ Checks if particular snmp command needs to be sent out """
        if self._system_settings.snmp_enable:
            # Figure out if Send SNMP Command condition exists
            snmp_agent = self['error']['_snmp'][error_field][error_code]['agent']
            if snmp_agent is not None:
                snmp_clear_command = self['error']['_snmp'][error_field][error_code]['clear']
                if snmp_clear_command is not None:

                    self.clear_snmp(snmp_agent, snmp_clear_command)
