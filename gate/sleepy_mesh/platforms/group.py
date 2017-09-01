"""
Group Class, contains list of nodes
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import os
import copy
import logging

from py_knife.ordered_dict import OrderedDict

from gate.conversions import internal_name, fetch_item, load_from_cookie
from gate.sleepy_mesh.node import HeaderMixin
from gate.sleepy_mesh.error import NodeError

from base import PlatformBase
from nodes import GroupNodes


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Group(PlatformBase, HeaderMixin):
    def __init__(self, group_name, platform_name, nodes):
        self.system_settings = nodes.system_settings
        self._nodes = nodes

        db_file_prefix = None
        if internal_name(group_name) != 'inactive_group':
            db_file_prefix = os.path.join('platforms', platform_name, 'groups')

        # Default Cookies
        defaults_kwargs = {
            'group': internal_name(group_name),
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
    def read_headers(self, header_type, nodes=None):
        """ Reads Headers for a particular group """
        output = {}

        if nodes is None:
            nodes = self.nodes.values()

        if len(nodes):
            first_node = nodes[0]
            sensor_type = self.__sensor_type(nodes)
            # LOGGER.debug('sensor_type: {}'.format(sensor_type))

            output = first_node.headers.read(header_type, sensor_type)

        return output

    def header_group(self, header_key, nodes=None):
        """ Returns header group for a particular header """
        output = None

        if nodes is None:
            nodes = self.nodes.values()

        if len(nodes):
            first_node = nodes[0]
            sensor_type = self.__sensor_type(nodes)
            # LOGGER.debug('sensor_type: {}'.format(sensor_type))

            output = first_node.headers.header_group(header_key, sensor_type)

        return output

    def __sensor_type(self, nodes=None):
        """ Determine sensor type of the group """
        if nodes is None:
            nodes = self.nodes.values()

        first_node = nodes[0]
        sensor_type = first_node['sensor_type']

        if len(nodes) > 1:
            sensor_type = list(sensor_type)
            for node in nodes:
                for sensor_index, sensor_code in enumerate(sensor_type):
                    if node['sensor_type'][sensor_index] != sensor_code:
                        sensor_type[sensor_index] = ' '

        return sensor_type

    # TODO: Move this whole cookie business out of here!!!
    ## Cookie Methods ##
    def default_cookie(self, page_type):
        """ Creates default cookie for a particular group """

        cookie = copy.deepcopy(self[page_type + '_cookie'])
        cookie['headers'] = {}

        all_headers = self.read_headers('all')
        for header_name, header in all_headers.items():
            header_cookie = copy.deepcopy(header[page_type + '_cookie'])
            cookie['headers'][header_name] = header_cookie

        return cookie

    ## Headers, Header and Unit Selection Methods ##
    def live_headers(self, nodes=None):
        """ Fetch enabled headers for the live page """
        return self.__enabled_headers('live', nodes)

    def log_headers(self, nodes=None):
        """ Fetch enabled headers for the log page """
        return self.__enabled_headers('log', nodes)

    def __enabled_headers(self, page_type, nodes=None):
        """ Fetch enabled headers """
        header_dict = OrderedDict()

        if nodes is None:
            nodes = self.nodes.values()

        display_headers = self.read_headers('display', nodes)
        for header_name, header in display_headers.items():
            for node in nodes:
                if header.enables(node, page_type + '_enables'):
                    header_dict[header_name] = header
                    break

        # LOGGER.debug('page_type: {}'.format(page_type))
        # LOGGER.debug('nodes: {}'.format(nodes.keys()))
        # LOGGER.debug('headers: {}'.format(header_dict.keys()))

        return header_dict

    def live_header(self, cookie, nodes=None):
        """ Returns selected header or set of headers on the live page """
        return self.__selected_header(cookie, 'live', nodes)

    def log_header(self, cookie, nodes=None):
        """ Returns selected header or set of headers on the log page """
        return self.__selected_header(cookie, 'log', nodes)

    def __selected_header(self, cookie, page_type, nodes=None):
        """ Returns selected header or set of headers """
        address = [
            'platforms', self['platform'], self['group'], 'selected']
        _cookie = load_from_cookie(cookie, address)

        if _cookie is None:
            LOGGER.warning("Using default cookies during '__selected' execution!")
            # LOGGER.warning('address: {}'.format(address))
            # LOGGER.warning('cookie: {}'.format(cookie))
            _cookie = self.default_cookie(page_type)

        # Read portion
        if page_type == 'live':
            output = None

            header_index = _cookie['selected']

            # # Multiple Hack
            # if 'multiple' in header_index:
            #     header_index = int(header_index.split('_')[-1])
            # # LOGGER.debug('header_index: {}'.format(header_index))

            display_headers = self.read_headers('display', nodes)
            _output = fetch_item(display_headers, header_index)
            if _output is not None:
                output = _output
        else:
            output = OrderedDict()

            selected_nodes = _cookie['selected']
            for net_addr in selected_nodes:
                output[net_addr] = OrderedDict()

                if net_addr in self.nodes.keys():
                    node = self.nodes[net_addr]
                    node_headers = selected_nodes[net_addr]
                    for header_index in node_headers:

                        # # Multiple Hack
                        # if 'multiple' in header_index:
                        #     header_index = int(header_index.split('_')[-1])
                        # # LOGGER.debug('header_index: {}'.format(header_index))

                        display_headers = node.read_headers('display')
                        _output = fetch_item(display_headers, header_index)
                        if _output is not None:
                            output[net_addr][_output['internal_name']] = _output

        return output

    def enables_masks(self, enable_type, enable_dict):
        """ Generates enables masks using enable dictionary """
        set_mask, clear_mask = 0, 0

        if enable_type in ('live_enables', 'log_enables', 'diag_enables'):
            # Convert to node enables
            all_headers = self.read_headers('all')
            for header in all_headers.values():
                header_mask = 1 << header['header_position']

                if header['internal_name'] in enable_dict:
                    bit_value = enable_dict[header['internal_name']]
                    if bit_value is not None:
                        if bit_value:
                            set_mask |= header_mask
                        else:
                            clear_mask |= header_mask

            # LOGGER.debug('{} dict: {}'.format(enable_type, enable_dict))
            # LOGGER.debug('enable_mask: {}'.format(output))

        else:
            LOGGER.error("Enable type '{}' does not exist!".format(enable_type))

        return set_mask, clear_mask

    def refresh(self):
        """ Refreshes diagnostic fields """
        for node in self.nodes.values():
            node.headers.refresh(node)

    ## Overloading Generic Macros ##
    def __getitem__(self, key):
        if key == 'group':
            key = 'internal_name'

        return super(Group, self).__getitem__(key)
