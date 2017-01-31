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
from header.common import fetch_item


### CONSTANTS ###
ALARM_HEADER_KEY_MAP = {
    'sensor_fault': 'data_field_position',
    'alarms': 'header_position'
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
## Data Type Classes ##
class Headers(DatabaseDict):
    """ Headers class responsible for a group of headers """
    def __init__(self, platform, display_headers, diagnostics_headers):
        """ Initializes headers """
        defaults = {
            'platform': platform,
            # Default Cookies
            'live_cookie': {'selected': 0},
            'log_cookie': {'selected': []}
        }
        db_file = platform + '_headers.db'

        super(Headers, self).__init__(
            db_file=db_file,
            defaults=defaults
        )
        self._display = OrderedDict()
        self._diagnostics = OrderedDict()

        self.__write('display', display_headers)
        self.__write('diagnostics', diagnostics_headers)

        self.header_defaults = self.__create_defaults()

        # LOGGER.debug("header_defaults['enables'].keys() = " + str(self.header_defaults['enables'].keys()))

    def __create_defaults(self):
        """ Generates defaults for particular platform """
        output = {
            'platform': self['platform'],
            'constants': {},
            'data_out': {},
            'alarms': {},
            'enables': {},
        }

        # Create top level structure
        all_headers = self.read('all').values()
        diagnostics_headers = self.read('diagnostics').keys()
        for header in all_headers:
            header_field = header['data_field']
            header_nickname = header['header_nickname']
            header_enable = bool(header['internal_name'] in diagnostics_headers)

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
                'alarms': header_nickname,
                'enables': header_nickname
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
                                    LOGGER.debug('alarm_units: ' + str(unit_name))
                                    LOGGER.debug('alarm_value: ' + str(unit_value[alarm_type]))
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
                    for enable_type in ('live_enable', 'log_enable', 'const_set'):
                        # Fill in enables variables
                        enable_value = (header_enable and enable_type != 'log_enable')
                        header.enables(output, enable_type, enable_value)

        return output

    def __read_write(self, header_type, new_headers=None):
        output = None
        if header_type in ('all', 'display', 'diagnostics'):
            _header_type = '_' + header_type
            # Write Portion
            if new_headers is not None:
                if header_type in ('display', 'diagnostics'):
                    for header_position, header_kwargs in enumerate(new_headers):
                        new_header_kwargs = {
                            'platform': self['platform'],
                            'header_type': header_type,
                            'header_position': header_position
                        }
                        new_header_kwargs.update(header_kwargs)
                        header = Header(**new_header_kwargs)
                        getattr(self, _header_type)[header['internal_name']] = header
                else:
                    LOGGER.error("Can not use 'all' header type to overwrite headers. " +
                                 "Please use either display or diagnostics header types instead!")
            # Read portion
            if header_type == 'all':
                output = OrderedDict()
                for header_type in ('display', 'diagnostics'):
                    _header_type = '_' + header_type
                    for header_key in getattr(self, _header_type).keys():
                        output[header_key] = getattr(self, _header_type)[header_key]
            else:
                output = getattr(self, _header_type)

        else:
            LOGGER.error("Header type " + str(header_type) + " does not exist!")

        return output

    def read(self, header_type):
        return self.__read_write(header_type)

    def __write(self, *args):
        return self.__read_write(*args)

    def default_cookie(self, page_type):
        """
        Returns Default cookies for all headers

        :return:
        """
        platform_cookie = {}

        if page_type in ('live', 'log'):
            platform_cookie = copy.deepcopy(self[page_type + '_cookie'])
            platform_cookie['headers'] = {}

            all_headers = self.read('all')
            for header_name, header in all_headers.items():
                platform_cookie['headers'][header_name] = header.default_cookie(page_type)

        else:
            LOGGER.error("Page type: " + str(page_type) + " does not exist!")

        return platform_cookie

    def selected(self, cookie, page_type):
        """
        :param cookie:
        :return: Selected header or set of headers
        """
        output = None
        if page_type == 'log':
            output = {}
        platform_cookie = None

        if page_type in ('live', 'log'):
            if 'platforms' in cookie and self['platform'] in cookie['platforms']:
                _platform_cookie = cookie['platforms'][self['platform']]
                if 'selected' in _platform_cookie:
                    platform_cookie = _platform_cookie

            if platform_cookie is None:
                LOGGER.warning("Using default cookies during 'selected' execution!")
                # LOGGER.debug("cookie = " + str(cookie))
                platform_cookie = self.default_cookie(page_type)

            # Read portion
            display_headers = self.read('display')
            if page_type == 'live':
                header_index = platform_cookie['selected']
                _output = fetch_item(display_headers, header_index)
                if _output is not None:
                    output = _output
            else:
                selected_nodes = platform_cookie['selected']
                for net_addr in selected_nodes:
                    output[net_addr] = OrderedDict()
                    node_headers = selected_nodes[net_addr]
                    for header_index in node_headers:
                        _output = fetch_item(display_headers, header_index)
                        if _output is not None:
                            output[net_addr][_output['internal_name']] = _output

        else:
            LOGGER.error("Page type: " + str(page_type) + " does not exist!")

        return output

    # Alert Messages #
    def alert_messages(self, alert_group):
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
                    error_field = error_register + '_' + header['header_type']
                    for alarm_type_index, alarm_type in enumerate(('min_alarm', 'max_alarm')):
                        warning_description = header['alert_messages'][error_register][alarm_type]
                        if error_register in ALARM_HEADER_KEY_MAP:
                            header_key = ALARM_HEADER_KEY_MAP[error_register]
                            if header[header_key] is not None:
                                error_code = header[header_key] * 2 + alarm_type_index
                                if warning_description is not None:
                                    output[error_field + '-' + str(error_code)] = warning_description

        return output


class NodeHeaders(Headers):
    def update_enables(self, page_type, node, enable_dict):
        """ Updates header enables """
        enable_value = 0

        if page_type in ('live', 'log'):
            # Convert to node enables
            all_headers = self.read('all').values()
            for header in all_headers:
                header_mask = None
                if header['data_field_position'] is not None:
                    header_mask = 1 << header['data_field_position']

                if header['internal_name'] in enable_dict:
                    bit_value = enable_dict[header['internal_name']]
                    # Compose node enables
                    if bit_value is not None and header_mask is not None:
                        if bit_value:
                            enable_value |= header_mask
                        else:
                            enable_value |= node[page_type + '_enable'] & header_mask

                    # Update headers
                    if bit_value is not None:
                        header.enables(node, page_type + '_enable', bit_value)

            # LOGGER.debug(page_type + "_enable = " + str(enable_dict))
            # LOGGER.debug("enable_value = " + str(enable_value))

        else:
            LOGGER.error("Page type: " + str(page_type) + " does not exist!")

        return enable_value

    def node_enables(self, page_type, node, overwrite_headers=False):
        """ Generates node enables from header enables """
        enable_value = 0

        if page_type in ('live', 'log'):
            # Convert to node enables
            all_headers = self.read('all').values()
            for header in all_headers:
                if header['data_field_position'] is not None:
                    header_mask = 1 << header['data_field_position']
                    if overwrite_headers:
                        header_enable = bool(node[page_type + '_enable'] & header_mask > 0)
                        header.enables(node, page_type + '_enable', header_enable)

                    if header.enables(node, page_type + '_enable'):
                        enable_value |= header_mask

            # LOGGER.debug(page_type + "_enable = " + str(enable_dict))
            # LOGGER.debug("enable_value = " + str(enable_value))

        else:
            LOGGER.error("Page type: " + str(page_type) + " does not exist!")

        return enable_value

    def enabled(self, page_type, nodes):
        """ Fetch enabled headers """
        header_dict = OrderedDict()

        if page_type in ('live', 'log'):
            display_headers = self.read('display')
            for header_name, header in display_headers.items():
                for node in nodes.values():
                    if header.enables(node, page_type + '_enable'):
                        header_dict[header_name] = header
                        break
        else:
            LOGGER.error("Page type: " + str(page_type) + " does not exist!")

        # LOGGER.debug('page_type: ' + str(page_type))
        # LOGGER.debug('nodes: ' + str(nodes.keys()))
        # LOGGER.debug('headers: ' + str(header_dict.keys()))

        return header_dict
