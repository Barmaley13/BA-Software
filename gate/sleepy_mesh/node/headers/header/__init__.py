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

from gate.conversions import fetch_item
from gate.strings import FIELD_UNIT

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
LOGGER.setLevel(logging.ERROR)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Header(HeaderBase):
    """ Header class holding constants, variables, units and modbus units as well as number of methods """
    def __init__(self, name, data_field, header_position, groups, **kwargs):
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
                        'header_name': name,
                        'header_position': header_position
                    }
                    new_group_kwargs.update(group_kwargs)
                    item_value = group_class(**new_group_kwargs)
                    item_key = item_value['internal_name']
                    getattr(self, group_name)[item_key] = item_value

        # print('name: {}'.format(name))
        # print('constants: {}'.format(len(self.constants)))
        # print('variables: {}'.format(len(self.variables)))
        # print('unit_list: {}'.format(len(self.unit_list)))

        # Initialize Defaults
        defaults = {
            # Global Must Haves
            'name': name,
            'data_field': data_field,
            'header_name': name,
            'header_position': header_position,
            'diagnostics': False,
            '_external': True,

            # Default Cookies
            'live_cookie': {'units': 0, 'table_units': [0]},
            'log_cookie': {'units': 0, 'table_units': [0]},

            # Except this one of course!
            'modbus_units': 0
        }

        defaults.update(kwargs)
        super(Header, self).__init__(**defaults)

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
                    check_alarm_enable = True
                    if group_variable['_external']:
                        _alarm_units = self.alarm_units(provider)
                        if _alarm_units is not None:
                            _alarm_name = _alarm_units['internal_name']
                            check_alarm_enable = bool(_alarm_name == group_variable['internal_name'])
                        else:
                            check_alarm_enable = False

                    if check_alarm_enable:
                        # LOGGER.debug('Group Variable: {} Field: {} Header: {}'.format(
                        #     group_variable['name'], field, self['internal_name']))

                        # Check/Clear Alarms
                        for alarm_type in ('min_alarm', 'max_alarm'):
                            alarm_triggered = group_variable.check_alarm(provider, calculated_value, alarm_type)
                            header_enable = self.enables(provider, 'live_enable')
                            header_enable |= self.enables(provider, 'diagnostics')
                            alarm_enable = group_variable.alarm_enable(provider, alarm_type)

                            if alarm_triggered and header_enable:
                                self._set_alarm(provider, group_variable, alarm_type)
                                # LOGGER.debug("*** " + alarm_type + " Set! ***")

                            elif alarm_enable or group_variable['_external']:
                                self._clear_alarm(provider, group_variable, alarm_type)
                                # LOGGER.debug("*** " + alarm_type + " Clear! ***

    def _set_alarm(self, provider, group_variable, alarm_type):
        """ Set Alarm """
        # Determine Register
        if group_variable['_external']:
            error_register = 'alarms'
            alarm_mask_key = 'header_position'
        else:
            error_register = 'sensor_fault'
            alarm_mask_key = 'data_field_position'

        # Alarm Error Code
        error_field = error_register + '_' + alarm_type
        error_code = self[alarm_mask_key]

        # Alarm Error Message
        if 'net_addr' in provider and provider['net_addr'] is not None:
            error_message = OF_NODE1 + provider['name'] + OF_NODE2
        else:
            error_message = provider['name'] + ' '

        # Extend Message (if needed)
        alarm_message = group_variable.alarm_message(alarm_type)
        if alarm_message:
            error_message += alarm_message

        provider.error.set_error(error_field, error_code, error_message)

    def _clear_alarm(self, provider, group_variable, alarm_type):
        """ Clear Alarm """
        # Determine Register
        if group_variable['_external']:
            error_register = 'alarms'
            alarm_mask_key = 'header_position'
        else:
            error_register = 'sensor_fault'
            alarm_mask_key = 'data_field_position'

        # Alarm Error Code
        error_field = error_register + '_' + alarm_type
        error_code = self[alarm_mask_key]

        provider.error.clear_error(error_field, error_code)

    ## Alarm Message ##
    def alarm_messages(self, error_register, alarm_type):
        """ Fetch alarm messages for this particular header """
        output = None

        field_types = {'alarms': 'unit_list', 'sensor_fault': 'variables'}
        if error_register in field_types.keys():
            if alarm_type in ('min_alarm', 'max_alarm'):

                for group_variable in getattr(self, field_types[error_register]).values():
                    if error_register == 'alarms':
                        check_alarm_message = self['diagnostics'] is False
                    else:
                        check_alarm_message = group_variable.alarm_enable(None, alarm_type)

                    if check_alarm_message:
                        output = group_variable.alarm_message(alarm_type)
                        if output is not None:
                            break

        return output

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

    def units(self, unit_index):
        return fetch_item(self.unit_list, unit_index)

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
                provider['alarms'][self['header_position']]['alarm_units'] = new_unit_index

        # Read portion
        unit_index = provider['alarms'][self['header_position']]['alarm_units']

        output = fetch_item(self.unit_list, unit_index)

        return output

    ## External Constants ##
    def external_constants(self):
        """
        Returns True or False depending if there are constants available for user editing.
        :return:
        """
        output = False

        for _constant in self.constants.values():
            if _constant['_external']:
                output = True
                break

        return output

    ## Misc ##
    def selected(self, sensor_type):
        output = False

        # LOGGER.debug('sensor_code: {}'.format(self['sensor_code']))
        # LOGGER.debug('sensor_type: {}'.format(sensor_type))
        # LOGGER.debug('data_field_position: {}'.format(self['data_field_position']))

        if 'sensor_code' in self._main:
            output = self['sensor_code'][-1] == sensor_type[self['data_field_position']]

        return output
