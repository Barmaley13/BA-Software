"""
Group Class, contains list of nodes
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import copy
import os
import logging

from py_knife.ordered_dict import OrderedDict

from gate.conversions import internal_name, fetch_item, load_from_cookie
from gate.sleepy_mesh.error import NodeError

from base import PlatformBase
from nodes import GroupNodes


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Group(PlatformBase):
    def __init__(self, group_name, platform_name, nodes):
        self.system_settings = nodes.system_settings
        self._nodes = nodes

        db_file_prefix = None
        if internal_name(group_name) != 'inactive_group':
            db_file_prefix = os.path.join('platforms', platform_name, 'groups')

        # Default Cookies
        defaults_kwargs = {
            'live_cookie': {'selected': 0},
            'log_cookie': {'selected': []}
        }

        super(Group, self).__init__(
            group_name, platform_name, db_file_prefix, **defaults_kwargs)

        nodes_db_file = None
        error_db_file = None
        if internal_name(group_name) != 'inactive_group':
            db_path = os.path.join('platforms', platform_name, 'groups', self['internal_name'])
            nodes_db_file = os.path.join(db_path, 'nodes.db')
            error_db_file = os.path.join(db_path, 'default_error.db')

        self.nodes = GroupNodes(
            self._nodes,
            db_file=nodes_db_file
        )

        self.error = NodeError(
            system_settings=self.system_settings,
            db_file=error_db_file
        )

    def save(self, db_content=None):
        """ Overloading default save method """
        self.nodes.save()
        super(Group, self).save()

    def delete(self):
        """ Overloading default delete method """
        self.nodes.delete()
        super(Group, self).delete()

    ## Header Related Methods ##
    def read_headers(self, header_type):
        """ Reads Headers for a particular group """
        output = {}

        if len(self.nodes):
            first_node = self.nodes.values()[0]
            sensor_type = self.__sensor_type()

            # LOGGER.debug('sensor_type: {}'.format(sensor_type))
            output = first_node.headers.read(header_type, sensor_type)

        return output

    def header_group(self, header_key):
        """ Returns header group for a particular header """
        output = None

        if len(self.nodes):
            first_node = self.nodes.values()[0]
            sensor_type = self.__sensor_type()

            output = first_node.headers.header_group(header_key, sensor_type)

        return output

    def __sensor_type(self):
        """ Determine sensor type of the group """
        first_node = self.nodes.values()[0]
        sensor_type = list(first_node['sensor_type'])

        if len(self.nodes) > 1:
            for node in self.nodes.values():
                for sensor_index, sensor_code in enumerate(sensor_type):
                    if node['sensor_type'][sensor_index] != sensor_code:
                        sensor_type[sensor_index] = None

        return sensor_type

    def enabled_headers(self, page_type):
        """ Fetch enabled headers """
        header_dict = OrderedDict()

        if page_type in ('live', 'log'):
            display_headers = self.read_headers('display')
            for header_name, header in display_headers.items():
                for node in self.nodes.values():
                    if header.enables(node, page_type + '_enable'):
                        header_dict[header_name] = header
                        break
        else:
            LOGGER.error("Page type '{}' does not exist!".format(page_type))

        # LOGGER.debug('page_type: ' + str(page_type))
        # LOGGER.debug('nodes: ' + str(nodes.keys()))
        # LOGGER.debug('headers: ' + str(header_dict.keys()))

        return header_dict

    def default_cookie(self, page_type):
        cookie = {}

        if page_type in ('live', 'log'):
            cookie = copy.deepcopy(self[page_type + '_cookie'])
            cookie['headers'] = {}

            all_headers = self.read_headers('all')
            for header_name, header in all_headers.items():
                cookie['headers'][header_name] = header.default_cookie(page_type)

        else:
            LOGGER.error("Page type: " + str(page_type) + " does not exist!")

        return cookie

    def selected_header(self, cookie, page_type):
        """ Returns selected header or set of headers """
        output = None
        if page_type == 'log':
            output = {}

        if page_type in ('live', 'log'):
            address = ('platforms', self['platform'], self['internal_name'], 'selected')
            _cookie = load_from_cookie(cookie, address)

            if _cookie is None:
                LOGGER.warning("Using default cookies during 'selected' execution!")
                # LOGGER.debug("cookie = " + str(cookie))
                _cookie = self.default_cookie(page_type)

            # Read portion
            display_headers = self.read_headers('display')
            if page_type == 'live':
                header_index = _cookie['selected']
                _output = fetch_item(display_headers, header_index)
                if _output is not None:
                    output = _output
            else:
                selected_nodes = _cookie['selected']
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

    def live_units(self, cookie, header_name):
        """ Returns currently selected units for the bar graph on live page """
        return self._units(cookie, header_name, 'live', 'units')

    def log_units(self, cookie, header_name):
        """ Returns currently selected units for the bar graph on live page """
        return self._units(cookie, header_name, 'log', 'units')

    def live_table_units(self, cookie, header_name):
        """ Returns currently selected list of units for the logs """
        return self._units(cookie, header_name, 'live', 'table_units')

    def log_table_units(self, cookie, header_name):
        """ Returns currently selected list of units for the logs """
        return self._units(cookie, header_name, 'log', 'table_units')

    def _units(self, cookie, header_name, page_type, units_type):
        """ Returns currently selected units for the bar graph on live page """
        output = None
        if units_type == 'table_units':
            output = OrderedDict()

        if page_type in ('live', 'log'):
            address = (
                'platforms', self['platform'], self['internal_name'], 'headers', header_name, units_type)
            _cookie = load_from_cookie(cookie, address)

            header = None
            display_headers = self.read_headers('display')
            for _header_name, _header in display_headers.items():
                if header_name == _header_name:
                    header = _header
                    break

            if header is not None:
                if _cookie is None:
                    LOGGER.warning("Using default cookies during 'selected' execution!")
                    # LOGGER.debug("cookie = " + str(cookie))
                    _cookie = header.default_cookie(page_type)

                # Read portion
                if units_type == 'units':
                    unit_index = _cookie[units_type]
                    _output = header.units(unit_index)
                    if _output is not None:
                        output = _output

                elif units_type == 'table_units':
                    for unit_index in _cookie[units_type]:
                        _output = header.units(unit_index)
                        if _output is not None:
                            output[_output['internal_name']] = _output
            else:
                LOGGER.error("Header: " + str(header_name) + " does not exist!")

        else:
            LOGGER.error("Page type: " + str(page_type) + " does not exist!")

        return output
