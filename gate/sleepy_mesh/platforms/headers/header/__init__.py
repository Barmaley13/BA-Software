"""
Header Package

Throughout this module we are using term "provider". It can means node instance or it also
could mean statistics instance.
"Provider" provides data that this header (aka Data Processor) processes.
Once the process of processing is done, it injects output data back into data provider.
We know that it is probably not the best practice to modify provider without its knowledge.
We will strive to improve our code and eliminate this condition in the near future.
"""

### INCLUDES ###
import copy
import logging

from py_knife.ordered_dict import OrderedDict

from gate.strings import FIELD_UNIT

from common import OPEN_CIRCUIT, SHORT_CIRCUIT, fetch_item
from base import HeaderBase
from constant import HeaderConstant
from variable import HeaderVariable
from unit import HeaderUnit


### CONSTANTS ###
## Strings ##
OF_NODE1 = FIELD_UNIT + " '"
OF_NODE2 = "' "

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Header(HeaderBase):
    """ Header class holding constants, variables, units and modbus units as well as number of methods """
    def __init__(self, data_field, platform, header_type, header_position, groups, **kwargs):
        """
        Initializes header

        :param groups: Provide dictionary with lists of ``constants``, ``variables``, ``units`` and ``modbus`` units
        :param live_units: Specify which unit is selected by default by specifying unit index.
        :return: Header instance
        """
        # Initialize Groups
        self.constants = OrderedDict()
        self.variables = OrderedDict()
        self.unit_list = OrderedDict()

        group_fields = {
            'constants': HeaderConstant,
            'variables': HeaderVariable,
            'unit_list': HeaderUnit
        }

        for group_name, group_class in group_fields.items():
            # Dynamically create attributes
            if group_name in groups:
                for group_kwargs in groups[group_name]:
                    new_group_kwargs = {
                        'data_field': data_field,
                        'platform': platform,
                        'header_type': header_type,
                        'header_position': header_position
                    }
                    new_group_kwargs.update(group_kwargs)
                    item_value = group_class(**new_group_kwargs)
                    item_key = item_value['internal_name']
                    getattr(self, group_name)[item_key] = item_value

        # print "name = " + name
        # print "constants = " + str(len(self.constants))
        # print "variables = " + str(len(self.variables))
        # print "unit_list = " + str(len(self.unit_list))

        # Initialize Defaults
        defaults = {
            # Global Must Haves
            'data_field': data_field,
            'platform': platform,
            'header_type': header_type,
            'header_position': header_position,
            # Default Cookies
            'live_cookie': {'units': 0, 'table_units': [0]},
            'log_cookie': {'units': 0, 'table_units': [0]},

            # Except this one of course!
            'modbus_units': 0
        }

        defaults.update(kwargs)
        super(Header, self).__init__(**defaults)

        self.update({
            # Alarm Messages
            'alert_messages': {
                'sensor_fault': {
                    'min_alarm': self._alert_message('sensor_fault', 'min_alarm'),
                    'max_alarm': self._alert_message('sensor_fault', 'max_alarm')
                },
                'alarms': {
                    'min_alarm': self._alert_message('alarms', 'min_alarm'),
                    'max_alarm': self._alert_message('alarms', 'max_alarm')
                }
            }
        })

        # print "Alert Messages: ", str(self['alert_messages'])

    ## Formula Related ##
    def apply_formulas(self, provider):
        """
        Applies formulas to all fields such as ``variables``, ``units``, ``modbus`` and
        updates data provider with the results.

        :param provider: data provider that we are working with
        :return: NA, provider['data_out'] is updated with new data
        """
        # Apply Formulas
        for field in ('variables', 'unit_list'):
            for group_variable in getattr(self, field).values():
                # Recalculate all variables
                if self.enables(provider, 'const_set'):
                    calculated_value = group_variable.apply_formula(provider)

                    # We need to filter proper group_variables that apply for checking/clearing alarms
                    for alarm_type in ('min_alarm', 'max_alarm'):
                        check_alarm_enable = False
                        if group_variable['_external']:
                            _alarm_name = self.alarm_units(provider)['internal_name']
                            check_alarm_enable |= bool(group_variable['internal_name'] == _alarm_name)
                        else:
                            check_alarm_enable |= bool(group_variable[alarm_type] is not None)

                        if check_alarm_enable:
                            LOGGER.debug("\nGroup Variable: " + str(group_variable['name']) +
                                         ' Field: ' + str(field) +
                                         ' Header: ' + str(self['internal_name']))
                            # Check/Clear Alarms
                            self._check_alarms(provider, group_variable, calculated_value, alarm_type)

    # TODO: Combine similarities in _check_alarms and _clear_alarms
    def _check_alarms(self, provider, group_variable, calculated_value, alarm_type):
        """
        Checks if any alarms or sensor circuitry faults has been triggered
        :return: NA
        """
        # Determine Register
        if group_variable['_external']:
            error_register = 'alarms'
            alarm_mask_key = 'header_position'
            error_message = self['name']
            alarm_enable = self.alarm_enable(provider, alarm_type)
        else:
            error_register = 'sensor_fault'
            alarm_mask_key = 'data_field_position'
            error_message = group_variable['name']
            alarm_enable = bool(group_variable[alarm_type] is not None)

        if 'net_addr' in provider and provider['net_addr'] is not None:
            error_message = OF_NODE1 + provider['name'] + OF_NODE2 + error_message
        else:
            error_message = provider['name'] + ' ' + error_message

        # Check for Error/Alarm/Fault
        _alarm_triggered = False
        if alarm_enable:
            # Fetch Alarm Threshold
            if group_variable['_external']:
                alarm_value = self.alarm_value(provider, alarm_type)
            else:
                alarm_value = group_variable[alarm_type]

            # LOGGER.debug("Alarm Value: " + str(alarm_value) + " Type: " + str(type(alarm_value)))
            # LOGGER.debug("Alarm Units: " + str(self.alarm_units(provider)['internal_name']))
            # LOGGER.debug("Calculated Value: " + str(calculated_value) +
            #              " Type: " + str(type(calculated_value)))
            # LOGGER.debug("Calculated Value Units: " + str(group_variable['internal_name']))

            # Check and Set Alarm
            if type(alarm_value) in (float, int) and type(calculated_value) in (float, int):
                if alarm_type == 'min_alarm':
                    # Min Alarm Check
                    _alarm_triggered = bool(calculated_value < alarm_value)
                elif alarm_type == 'max_alarm':
                    # Max Alarm Check
                    _alarm_triggered = bool(calculated_value > alarm_value)

                # Extend Message (if needed)
                if _alarm_triggered:
                    # LOGGER.debug("Alarm Type: " + str(alarm_type))
                    # LOGGER.debug("Generic Alarm Enable: " + str(generic_alarm_enabled))
                    # LOGGER.debug("User Alarm Enable: " + str(user_alarm_enabled))
                    # LOGGER.debug("Error Register: " + str(error_register))
                    # LOGGER.debug("Error Code: " + str(error_code))

                    # Report Error/Alarm/Fault (if any)
                    if group_variable[alarm_type + '_message']:
                        error_message += group_variable[alarm_type + '_message']

        # Set/Clear Alarm Error Code
        error_field = error_register + '_' + self['header_type']
        error_code = group_variable[alarm_mask_key] * 2 + ('min_alarm', 'max_alarm').index(alarm_type)

        if _alarm_triggered and self.enables(provider, 'live_enable'):
            provider.error.set_error(error_field, error_code, error_message)
            LOGGER.debug("*** " + alarm_type + " Set! ***")
        else:
            provider.error.clear_error(error_field, error_code)
            LOGGER.debug("*** " + alarm_type + " Clear! ***")

    ## Alarm Message ##
    def _alert_message(self, error_register, alarm_type):
        """ Fetch alarm messages for this particular header """
        alarm_message = None

        field_types = {'sensor_fault': 'variables', 'alarms': 'unit_list'}
        if error_register in field_types.keys():
            if alarm_type in ('min_alarm', 'max_alarm'):

                for group_variable in getattr(self, field_types[error_register]).values():
                    alarm_message = None
                    if group_variable[alarm_type] is not None or \
                            (error_register == 'alarms' and group_variable['header_type'] == 'display'):
                        if error_register == 'sensor_fault':
                            alarm_message = group_variable['name']
                        else:
                            alarm_message = self['name']

                        if alarm_message is not None:
                            if group_variable[alarm_type + '_message']:
                                alarm_message += group_variable[alarm_type + '_message']
                                break

        return alarm_message

    ## Default Cookie ##
    def default_cookie(self, page_type):
        """ Returns default header cookie """
        header_cookie = {}

        if page_type in ('live', 'log'):
            header_cookie = copy.deepcopy(self[page_type + '_cookie'])

        else:
            LOGGER.error("Page type: " + str(page_type) + " does not exist!")

        return header_cookie

    ## Selected Units ##
    def modbus_units(self, new_unit_index=None):
        """
        Returns currently selected units for the modbus output.
        Or alternatively sets new units for the modbus output.

        :param new_unit_index: internal name of the new units
        :return: currently selected units
        """
        # Write portion
        if new_unit_index is not None:
            _output = fetch_item(self.unit_list, new_unit_index)
            if _output is not None:
                self['modbus_units'] = new_unit_index
                self.save()

        # Read portion
        unit_index = self['modbus_units']

        output = fetch_item(self.unit_list, unit_index)

        return output

    def units(self, cookie=None, page_type='live'):
        """
        Returns currently selected units for the bar graph on live page.

        :return: currently selected units
        """
        return self._units(cookie, page_type, 'units')

    def table_units(self, cookie, page_type):
        """
        Returns currently selected list of units for the logs.

        :return: list of currently selected units
        """
        return self._units(cookie, page_type, 'table_units')

    def _units(self, cookie, page_type, units_type):
        """
        Returns currently selected units for the bar graph on live page.

        :return: currently selected units
        """
        output = None
        if units_type == 'table_units':
            output = OrderedDict()

        header_cookie = None
        if cookie is None:
            cookie = dict()

        elif type(cookie) in (str, unicode):
            if units_type == 'units':
                # TODO: Check that cookie string matches with a valid unit instance
                header_cookie = {'units': cookie}

        if page_type in ('live', 'log'):
            if header_cookie is None:
                if 'platforms' in cookie and self['platform'] in cookie['platforms']:
                    _platform_cookie = cookie['platforms'][self['platform']]

                    if 'headers' in _platform_cookie and self['internal_name'] in _platform_cookie['headers']:
                        _header_cookie = _platform_cookie['headers'][self['internal_name']]
                        if units_type in _header_cookie:
                            header_cookie = _header_cookie

            if header_cookie is None:
                LOGGER.warning("Using default cookies during '" + units_type + "' execution!")
                # LOGGER.debug("cookie = " + str(cookie))
                # LOGGER.debug('internal_name = ' + str(self['internal_name']))
                header_cookie = self.default_cookie(page_type)

            # Read portion
            if units_type == 'units':
                unit_index = header_cookie[units_type]
                _output = fetch_item(self.unit_list, unit_index)
                if _output is not None:
                    output = _output

            elif units_type == 'table_units':
                for unit_index in header_cookie[units_type]:
                    _output = fetch_item(self.unit_list, unit_index)
                    if _output is not None:
                        output[_output['internal_name']] = _output
        else:
            LOGGER.error("Page type: " + str(page_type) + " does not exist!")

        return output

    ## Alarm Related ##
    def alarm_units(self, provider, new_unit_index=None):
        """
        Either get or sets particular enable value

        :param provider: data provider that we are working with
        :param new_unit_index: provide None if reading, provide write value if writing
        :return: either read value or write value of the enable
        """
        # Write portion
        if new_unit_index is not None:
            _output = fetch_item(self.unit_list, new_unit_index)
            if _output is not None:
                provider['alarms'][self['header_nickname']]['alarm_units'] = new_unit_index

        # Read portion
        unit_index = provider['alarms'][self['header_nickname']]['alarm_units']

        output = fetch_item(self.unit_list, unit_index)

        return output

    def alarm_triggered(self, provider):
        """
        :return: True or False depending if alarm was triggered or not
        """
        alarm_mask = 1 << self['header_position'] * 2
        alarm_mask |= 1 << (self['header_position'] * 2 + 1)
        # LOGGER.debug("alarm_mask = " + str(alarm_mask))

        error_field = 'alarms_' + self['header_type']
        alarm_values = provider.error.get_error_alarm_register(error_field)
        # LOGGER.debug("alarm_values = " + str(alarm_values))

        _alarm_triggered = bool(alarm_values & alarm_mask > 0)
        # LOGGER.debug("_alarm_triggered = " + str(_alarm_triggered))

        return _alarm_triggered

    ## Sensor Fault Related ##
    def sensor_fault(self, provider):
        """
        :param provider:
        :return: either None or message that should be displayed
        """
        output = None

        if self['data_field_position'] is not None:
            error_field = 'sensor_fault_' + self['header_type']
            short_circuit_mask = 1 << self['data_field_position'] * 2
            open_circuit_mask = 1 << (self['data_field_position'] * 2 + 1)

            alarm_values = provider.error.get_error_alarm_register(error_field)
            if alarm_values & short_circuit_mask:
                output = str(self['name']) + SHORT_CIRCUIT
            elif alarm_values & open_circuit_mask:
                output = str(self['name']) + OPEN_CIRCUIT

        return output
