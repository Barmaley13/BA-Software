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

from common import fetch_item
from base import HeaderBase
from constant import HeaderConstant
from variable import HeaderVariable
from unit import HeaderUnit


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Header(HeaderBase):
    """ Header class holding constants, variables, units and modbus units as well as number of methods """
    def __init__(self, name, data_field, platform, header_type, header_position, groups, **kwargs):
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
                        'header_name': name,
                        'header_type': header_type,
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
            'platform': platform,
            'header_name': name,
            'header_type': header_type,
            'header_position': header_position,
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
                        _alarm_name = self.alarm_units(provider)['internal_name']
                        check_alarm_enable = bool(_alarm_name == group_variable['internal_name'])

                    if check_alarm_enable:
                        LOGGER.debug('Group Variable: {} Field: {} Header: {}'.format(
                            group_variable['name'], field, self['internal_name']))

                        # Check/Clear Alarms
                        group_variable.check_alarms(provider, calculated_value)

    ## Alarm Message ##
    def alarm_messages(self, error_register, alarm_type):
        """ Fetch alarm messages for this particular header """
        output = None

        field_types = {'alarms': 'unit_list', 'sensor_fault': 'variables'}
        if error_register in field_types.keys():
            if alarm_type in ('min_alarm', 'max_alarm'):

                for group_variable in getattr(self, field_types[error_register]).values():
                    if error_register == 'alarms':
                        check_alarm_message = group_variable['header_type'] == 'display'
                    else:
                        check_alarm_message = group_variable.alarm_enable(None, alarm_type)

                    if check_alarm_message:
                        output = group_variable.alarm_message(alarm_type)
                        if output is not None:
                            break

        return output

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

    def alarm_mask(self):
        """
        :return: Alarm Mask
        """
        output = 1 << self['header_position'] * 2
        output |= 1 << (self['header_position'] * 2 + 1)
        # LOGGER.debug("alarm_mask = " + str(output))

        return output

    def short_circuit_mask(self):
        """
        :return: Short Circuit Mask
        """
        output = 0

        if self['data_field_position'] is not None:
            output = 1 << self['data_field_position'] * 2

        return output

    def open_circuit_mask(self):
        """
        :return: Open Circuit Mask
        """
        output = 0

        if self['data_field_position'] is not None:
            output = 1 << (self['data_field_position'] * 2 + 1)

        return output
