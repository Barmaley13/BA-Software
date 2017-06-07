"""
Base Error Class
"""

### INCLUDES ###
import copy
import logging

from gate.database import DatabaseDict


### CONSTANTS ###
## Error Register Length ##
# Should be at least len(ADC_FIELDS)*2
# Dynamic value would be len(headers) (either display or diagnostics, whatever is bigger) * 2
LENGTH = 24

## Default SNMP Dictionary ##
# Working with lists and indexes just to test code!!!
DEFAULT_SNMP_DICT = {'agent': None, 'set': None, 'clear': None, 'trap': None}

## Error Register Structure ##
# Default Error Dictionary - Dynamic Generation #
DEFAULT_ERROR_DATA_TYPES = {
    '_alarms': 0x0000,
    '_acks': 0x0000,
    '_messages': [None] * LENGTH,
    '_time': [None] * LENGTH,
    '_new_error': [False] * LENGTH           # Flag that signalizes new errors
}

DEFAULT_ERROR_REGISTERS = {
    'sensor_fault_display': None,
    'sensor_fault_diagnostics': None,
    'alarms_display': None,
    'alarms_diagnostics': None
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def generate_default_error_dict(error_data_types, default_registers):
    """ Generates Default Error Dictionary """
    output = dict()
    for field_type, data_type in error_data_types.items():
        output[field_type] = copy.deepcopy(default_registers)
        for register_name, register_value in default_registers.items():
            if register_value is None:
                output[field_type][register_name] = copy.deepcopy(data_type)

    return output


### CLASSES ###
class BaseError(DatabaseDict):
    """ Methods related to Node Error Engine """
    def __init__(self, system_settings, **kwargs):
        self._system_settings = system_settings
        self._default_error_data_types = copy.deepcopy(DEFAULT_ERROR_DATA_TYPES)
        self._default_error_registers = copy.deepcopy(DEFAULT_ERROR_REGISTERS)

        super(BaseError, self).__init__(**kwargs)

    def load(self):
        """ Overloading base class load method """
        default_error_dict = generate_default_error_dict(
            self._default_error_data_types,
            self._default_error_registers
        )

        if self._defaults is None:
            self._defaults = dict()

        if 'error' not in self._defaults:
            self._defaults.update({
                'error': copy.deepcopy(default_error_dict)
            })

        if '_error_alarms' not in self._defaults:
            self._defaults.update({
                '_error_alarms': copy.deepcopy(default_error_dict['_alarms'])
            })

        super(BaseError, self).load()

    def update(self, value):
        """ Overloading base class method """
        super(BaseError, self).update(value)
        # Otherwise error gets linked to the update value
        self.save()
        self.load()

    ## Public Methods ##
    # Basic Error Methods #
    def set_error(self, error_field, error_code, error_message):
        """ Set error using single error code bit and error message """
        error_code = int(error_code)

        # LOGGER.debug('Set error code')
        # LOGGER.debug("error_field: " + str(error_field) + " error_code: " + str(error_code))

        error_mask = 1 << error_code
        self['error']['_alarms'][error_field] |= error_mask

        self._change_error_ack(error_field, error_code)
        self.__set_error_message(error_field, error_code, error_message)

    def clear_error(self, error_field, error_code):
        """ Clears error using single error code bit """
        error_code = int(error_code)

        # LOGGER.debug('Clear error code')
        # LOGGER.debug("error_field: " + str(error_field) + " error_code: " + str(error_code))

        error_mask = 1 << error_code
        self['error']['_alarms'][error_field] &= ~error_mask

        self._change_error_ack(error_field, error_code)
        self.__set_error_message(error_field, error_code, None)

    # Alarms #
    def get_error_alarm_register(self, error_field):
        """ Fetches error register """
        error_code = self['error']['_alarms'][error_field]

        return error_code

    # Error Codes, Warnings #
    # FIXME: Duplicate method? (Do we really need this?)
    def get_error_message(self, error_field):
        """ Fetches single error message """
        _error_list = self['error']['_messages'][error_field]
        # LOGGER.debug('Error list of ' + error_field + ': ' + str(_error_list))

        error_list = copy.deepcopy(_error_list)
        error_list = [error_value for error_value in error_list if error_value is not None]

        error_message = ''
        if len(error_list):
            error_message = error_list[0]

        return error_message

    def get_error_messages(self, provider_id):
        """ Fetches error messages """
        error_dict = dict()

        for error_field in self['error']['_messages'].keys():
            error_messages = self['error']['_messages'][error_field]
            error_acks = self['error']['_acks'][error_field]
            for error_code in range(len(error_messages)):
                error_message = error_messages[error_code]
                error_time = self['error']['_time'][error_field][error_code]
                new_error = self['error']['_new_error'][error_field][error_code]
                error_mask = 1 << error_code
                if error_message is not None and error_time is not None:
                    # if error_field == 'generic':
                    #     error_dict.clear()

                    error_dict[error_time] = {
                        'key': provider_id + '-' + error_field + '-' + str(error_code),
                        'time': self._system_settings.local_time(error_time),
                        'message': error_message,
                        'ack': bool(error_acks & error_mask),
                        'new': new_error
                    }

                    if new_error:
                        self['error']['_new_error'][error_field][error_code] = False

                    # if error_field == 'generic':
                    #     return error_dict

        return error_dict

    # Acks #
    def change_ack_state(self, error_field, error_code, ack_value):
        """ Changes state of specified ack. Triggered by user """
        self._change_error_ack(error_field, error_code, ack_value)

    ## Private Methods ##
    def _change_error_ack(self, error_field, error_code, ack_value=None):
        """
        Checks if error ack needs to be set or cleared
        Or forces set/clear if ack_value is not None
        """
        error_code = int(error_code)
        error_mask = 1 << error_code

        old_alarm_register = self['_error_alarms'][error_field]
        new_alarm_register = self['error']['_alarms'][error_field]

        set_ack = 0
        clear_ack = 0
        if ack_value is None:
            # Logical XOR #
            logical_xor = old_alarm_register ^ new_alarm_register

            # Set Ack bits #
            # Sets only on 0->1 transition
            set_ack = logical_xor & new_alarm_register & error_mask

            # Clear Ack bits #
            # Clears only on 1->0 transition
            clear_ack = logical_xor & old_alarm_register & error_mask
            # Clears when new error is 0
            # clear_ack = ~new_error & error_mask

        else:
            if ack_value:
                set_ack = new_alarm_register & error_mask
            else:
                clear_ack = new_alarm_register & error_mask

        if set_ack > 0:
            # LOGGER.debug("Set Ack")
            self._set_error_ack(error_field, error_code, ack_value)

        if clear_ack > 0:
            # LOGGER.debug("Clear Ack")
            self._clear_error_ack(error_field, error_code, ack_value)

        # if set_ack > 0 or clear_ack > 0:
        #     LOGGER.debug("error_field: " + str(error_field) + " error_code: " + str(error_code))

    def _set_error_ack(self, error_field, error_code, ack_value):
        """ Set Error Ack """
        error_mask = 1 << error_code
        self['error']['_acks'][error_field] |= error_mask

        if ack_value is None:
            self['error']['_time'][error_field][error_code] = self._system_settings.time()
            self['error']['_new_error'][error_field][error_code] = True

    def _clear_error_ack(self, error_field, error_code, ack_value):
        """ Clear Error Ack """
        error_mask = 1 << error_code
        self['error']['_acks'][error_field] &= ~error_mask

        if ack_value is None:
            # LOGGER.debug("New Clear Ack")
            self['error']['_time'][error_field][error_code] = None
            self['error']['_new_error'][error_field][error_code] = False

    def save_error_alarms(self):
        """ Saves Error alarms for future ack generation """
        self['_error_alarms'] = copy.deepcopy(self['error']['_alarms'])

    ## Class-Private Methods ##
    def __set_error_message(self, error_field, error_code, error_message):
        """ Sets error message """
        self['error']['_messages'][error_field][error_code] = error_message
