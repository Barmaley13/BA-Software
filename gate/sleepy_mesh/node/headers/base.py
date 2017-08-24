"""
Headers are responsible for interpreting raw data, applying formulas and different unit calculations
for the web display.

Raw data is parsed by :mod:`gate.sleepy_mesh.node.data` initially. Raw data consist of following fields:
``adc0``-``adc7``, ``lq``, ``temp`` and ``batt``. It is possible to have multiple headers assigned
to a single raw data entry. For example, currently on JOWA platform, ``adc0`` is used to
calculate both liquid level and liquid volume.

Each header declaration consist of declaring constants, variables, and units. Constants can be defined by user input
or be internal. Currently, constants are tied to raw data values. Meaning that it is possible to use same constants
across multiple headers that are tied to the same raw data field. For example, constants that are used for
liquid level calculations are also used for the liquid volume calculations.

Variable and units are for the most part are the same thing. The difference is that variables are
for internal use only. Units are variables that provide value externally via web interface. Each header can have
multiple units. For example, liquid volume can have options to output final value in liters or gallons.

Furthermore, there is a modbus declaration. Hopefully, we won't use it the near future. Has been created
to accommodate need to output modbus in different units/format. For the future release, we would like to stick to
outputting floating point in the units that are currently selected by user.

Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import copy
import logging

from py_knife.ordered_dict import OrderedDict

from gate.database import DatabaseDict
from gate.strings import FIELD_UNIT
from gate.sleepy_mesh.error import GENERIC_MESSAGES

from header import Header


### CONSTANTS ###
ALARM_HEADER_KEY_MAP = {
    'alarms': 'header_position',
    'sensor_fault': 'data_field_position'
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
## Data Type Classes ##
class Headers(DatabaseDict):
    """ Headers class responsible for a group of headers """
    def __init__(self, headers, sensor_type=None):
        """ Initializes headers """
        super(Headers, self).__init__()

        self._headers = []
        for header_position, header_group in enumerate(headers):
            if type(header_group) in (dict, OrderedDict):
                header_group = [header_group]

            self._headers.append(OrderedDict())
            for header_kwargs in header_group:
                header_kwargs.update({
                    'header_position': header_position
                })
                header = Header(**header_kwargs)

                if len(header_group) > 1:
                    header['internal_name'] += '_' + str(header_position)
                    header['_name'] = header_kwargs['name']

                self._headers[-1][header['internal_name']] = header

        if sensor_type:
            self.rename_headers(sensor_type)

        self.header_defaults = self.__create_defaults()

        # LOGGER.debug("header_defaults['enables'].keys() = " + str(self.header_defaults['enables'].keys()))

    def __create_defaults(self):
        """ Generates defaults for particular platform """
        output = {
            'constants': {},
            'data_out': {},
            'alarms': {},
            'enables': {},
        }

        # Create top level structure
        for header_group in self._headers:
            for header_key, header in header_group.items():
                header_field = header['data_field']
                header_enable = header['diagnostics']

                # Init constants and data_out structure
                for node_field in ('constants', 'data_out'):
                    if header_field not in output[node_field]:
                        output[node_field][header_field] = {}

                # Fill in constants
                for constant_name, constant_value in header.constants.items():
                    const_val = output['constants'][header_field]
                    const_val[constant_name] = constant_value.default_value()

                # Inject header names into structures
                main_fields = {
                    'constants': header_field,
                    'alarms': header['header_position'],
                    'enables': header['header_position']
                }
                for main_field, sub_field in main_fields.items():
                    if sub_field not in output[main_field]:
                        output[main_field][sub_field] = {}

                    # Fill in constants
                    if main_field == 'constants':
                        for constant_name, constant_value in header.constants.items():
                            if constant_name not in output[main_field][sub_field]:
                                output[main_field][sub_field][constant_name] = constant_value.default_value()

                    # Fill in alarms
                    elif main_field == 'alarms':
                        for alarm_type in ('min_alarm', 'max_alarm'):
                            if header_enable:
                                for unit_name, unit_value in header.unit_list.items():
                                    if alarm_type in unit_value and unit_value[alarm_type] is not None:
                                        # LOGGER.debug('alarm_units: ' + str(unit_name))
                                        # LOGGER.debug('alarm_value: ' + str(unit_value[alarm_type]))

                                        header.alarm_enable(output, alarm_type, True)
                                        header.alarm_value(output, alarm_type, unit_value[alarm_type])
                                        # Assumes same alarm units for min_alarm and max_alarm
                                        header.alarm_units(output, unit_name)
                                        break

                                else:
                                    header.alarm_enable(output, alarm_type, False)
                                    header.alarm_value(output, alarm_type, '')

                            else:
                                header.alarm_enable(output, alarm_type, False)
                                header.alarm_value(output, alarm_type, '')

                        output[main_field][sub_field]['alarm_units'] = 0

                    # Init enables
                    elif main_field == 'enables':
                        _external_constants = header.external_constants()
                        for enable_type in ('live_enable', 'log_enable', 'const_set'):
                            # Fill in enables variables
                            enable_value = (enable_type == 'const_set' and not _external_constants)
                            header.enables(output, enable_type, enable_value)

        return output

    def read(self, header_type, sensor_type):
        """ Read Headers """
        output = None

        if header_type in ('all', 'display', 'diagnostics'):
            if header_type == 'all':
                header_types = ('display', 'diagnostics')
            else:
                header_types = (header_type, )

            header_type_map = {True: 'diagnostics', False: 'display'}

            output = OrderedDict()
            for header_type in header_types:
                for header_group in self._headers:
                    for header_key, header in header_group.items():
                        if header_type == header_type_map[header['diagnostics']]:
                            header['selected'] = len(header_group) == 1
                            header['selected'] |= header.selected(sensor_type)
                            if header['selected']:
                                output[header_key] = header
                                break

        else:
            LOGGER.error("Header type " + str(header_type) + " does not exist!")

        return output

    def header_group(self, header_key, sensor_type):
        """ Returns header group for a particular header """
        output = None
        for _header_group in self._headers:
            if len(_header_group) > 1:
                if header_key in _header_group.keys():
                    output = copy.deepcopy(_header_group)

                    sensor_index = _header_group[header_key]['data_field_position']
                    if sensor_type[sensor_index] is not None:
                        del output[output.keys()[0]]

                    break

        return output

    def rename_headers(self, sensor_type):
        """ Renames headers after changing sensor code of a particular node """
        # Total count of repeating sensor indexes
        total_counter = {}
        for sensor_code in sensor_type:
            total_counter[sensor_code] = total_counter.get(sensor_code, -1) + 1

        # LOGGER.debug('total_counter: {}'.format(total_counter))

        current_counter = {}
        for header_group in self._headers:
            if len(header_group) > 1:
                for header in header_group.values():
                    if header.selected(sensor_type):
                        # LOGGER.debug('sensor_code: {}'.format(sensor_code))

                        # Reset name to default one
                        header['name'] = header['_name']

                        sensor_code = header['sensor_code'][-1]
                        if sensor_code in total_counter:
                            # Current count of repeating sensor indexes
                            current_counter[sensor_code] = current_counter.get(sensor_code, 0) + 1
                            if total_counter[sensor_code]:
                                # Append name count if needed
                                header['name'] += ' ' + str(current_counter[sensor_code])

                                # LOGGER.debug("header['name']: {}".format(header['name']))

        # LOGGER.debug('current_counter: {}'.format(current_counter))

    # Alarm Messages #
    def alarm_messages(self, alert_group):
        """ Fetch messages specified by group """
        output = OrderedDict()

        if alert_group in ('all', 'hardware'):
            error_field = 'generic'
            for error_code, error_message in GENERIC_MESSAGES.items():
                warning_description = FIELD_UNIT + error_message
                output[error_field + '-' + str(error_code)] = warning_description

        if alert_group != 'hardware':
            if alert_group == 'sensor_fault':
                error_registers = ('sensor_fault',)
            elif alert_group == 'alarms':
                error_registers = ('alarms',)
            else:
                error_registers = ('sensor_fault', 'alarms')

            if alert_group in ('sensor_fault', 'alarms'):
                headers = self.read('display').values()
            elif alert_group == 'diagnostics':
                headers = self.read('diagnostics').values()
            else:
                headers = self.read('all').values()

            for error_register in error_registers:
                for header in headers:
                    for alarm_type in ('min_alarm', 'max_alarm'):
                        error_field = error_register + '_' + alarm_type
                        warning_description = header.alarm_messages(error_register, alarm_type)
                        if error_register in ALARM_HEADER_KEY_MAP:
                            header_key = ALARM_HEADER_KEY_MAP[error_register]
                            if header[header_key] is not None:
                                error_code = header[header_key]
                                if warning_description is not None:
                                    output[error_field + '-' + str(error_code)] = warning_description

        return output
