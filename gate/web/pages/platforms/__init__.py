"""
Platforms Class
Basically class that interacts with Sleepy Mesh Platforms and Web Interface Internals (Pages, Json, etc)
Would not say it is a buffer, more of a translator between the two parties

Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""


### INCLUDES ###
import os
# import time
import copy
import urllib
import math
import logging

import bottle

from py_knife.ordered_dict import OrderedDict

from gate.common import LIVE_NODES_NUMBER
from gate.conversions import internal_name


### CONSTANTS ###
## Strings ##
# Page Title #
PAGE = "Page "

# Validation #
GROUP_VALIDATION = "*Group"

## Bottle Templates ##
_TEMPLATE_PATH = os.path.dirname(os.path.realpath(__file__))
bottle.TEMPLATE_PATH.append(_TEMPLATE_PATH)

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.ERROR)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def _url_encode(input_str):
    """ Modified url encode function for our application """
    output = urllib.quote(input_str, "")
    output = output.replace('-', '+')
    return output


def _url_decode(input_str):
    """ Modified url decode function for our application """
    output = input_str.replace('+', '-')
    output = urllib.unquote(output)
    return output


def _parse_url(address_str):
    """ Internal address string url parsing """
    platform = None
    group = None
    node_index = None

    if address_str is not None:
        address_list = address_str.split('-')
        if len(address_list) == 3:

            # Decode parts of the url
            for index, item in enumerate(address_list):
                address_list[index] = _url_decode(item)

            # Assign parts
            platform = address_list[0]
            group = address_list[1]
            node_index = int(address_list[2])

    return platform, group, node_index


def _header_select_html(header, header_group):
    """ Creates header selection drop down menu """
    output = ''

    if header_group is None:
        output += header['name']
    else:
        output += bottle.template(
            'header_selection_html', header=header, header_group=header_group)

    return output


def _header_html(header, nodes):
    """ Creates html for a particular header """
    output = ''

    for enable_type in ('live_enables', 'log_enables', 'diag_enables'):
        output += _enable_html(header, nodes, enable_type)

    for alarm_type in ('min_alarm', 'max_alarm'):
        output += _alarm_html(header, nodes, alarm_type)

    output += _alarm_units_html(header, nodes)

    return output


def _enable_html(header, nodes, enable_type):
    """ Create html for the enables """
    # start_time = time.time()

    output = ''

    if enable_type in ('live_enables', 'log_enables', 'diag_enables'):
        indeterminate = False
        check = None
        for node in nodes:
            enable = header.enables(node, enable_type)
            if check is None:
                check = enable
            else:
                indeterminate = bool(check != enable)
                if indeterminate:
                    check = False
                    break

        enable_data = {
            'name': header['internal_name'],
            'key': enable_type,
            'indeterminate': indeterminate,
            'check': check
        }
        # LOGGER.debug("enable_data = " + str(enable_data))

        output = bottle.template('enable_html', enable=enable_data)

    else:
        LOGGER.error("Enable type '{}' does not exist!".format(enable_type))

    # LOGGER.debug('_enable_html Time: ' + str(time.time() - start_time) + ' seconds')

    return output


def _alarm_html(header, nodes, alarm_type):
    """ Create html for the alarms """
    # start_time = time.time()

    output = ''

    if alarm_type in ('min_alarm', 'max_alarm'):
        alarm_enable = None
        indeterminate1 = False
        for node in nodes:
            node_alarm_enable = header.alarm_enable(node, alarm_type)
            if alarm_enable is None:
                alarm_enable = node_alarm_enable
            else:
                indeterminate1 = bool(alarm_enable != node_alarm_enable)
                if indeterminate1:
                    alarm_enable = False
                    break

        alarm_value = None
        indeterminate2 = bool(len(nodes) > 1)
        if not indeterminate2:
            alarm_value = header.alarm_value(nodes[0], alarm_type)

        alarm_units = header.alarm_units(nodes[0])
        min_value, max_value, alarm_step = '', '', ''
        if alarm_units is not None:
            min_value = str(alarm_units.get_min(nodes[0]))
            max_value = str(alarm_units.get_max(nodes[0]))
            alarm_step = str(alarm_units['step'])

        alarm_data = {
            'name': header['internal_name'],
            'enable': alarm_enable,
            'value': alarm_value,
            'units': alarm_units,
            'enable_name': alarm_type + '_enable',
            'value_name': alarm_type + '_value_' + header['internal_name'],
            'indeterminate1': indeterminate1,
            'indeterminate2': indeterminate2,
            'min_value': min_value,
            'max_value': max_value,
            'step': alarm_step,
            'disabled': bool(
                # not header.enables(nodes[0], 'live_enables') or
                not header.enables(nodes[0], 'const_set') or indeterminate2
            )
        }

        # LOGGER.debug("alarm_data = " + str(alarm_data))

        output = bottle.template('alarm_html', alarm=alarm_data)

    else:
        LOGGER.error("Alarm type: " + str(alarm_type) + " does not exist!")

    # print('Node Enables: {}'.format(nodes[0]['enables']))

    # LOGGER.debug('_alarm_html Time: ' + str(time.time() - start_time) + ' seconds')

    return output


def _alarm_units_html(header, nodes):
    """ Create alarm units html """
    # start_time = time.time()

    output = ''
    header_data = {
        'name': header['internal_name'],
        'nodes': nodes,
        'alarm_units': header.alarm_units(nodes[0]),
        'unit_list': header.unit_list,
        'disabled': bool(
            not header.enables(nodes[0], 'const_set') or len(nodes) > 1
        )
    }

    output += bottle.template('alarm_units_html', header=header_data)

    # LOGGER.debug('_alarm_units_html Time: ' + str(time.time() - start_time) + ' seconds')

    return output


def _constants_js(header, nodes):
    """
    Generate validation javascript for the constants of a particular node

    :param nodes: list of nodes that we are working with
    :return: js validation string
    """
    # start_time = time.time()

    output = []
    constants = nodes[0]['constants'][header['data_field']]

    for constant_key, constant in header.constants.items():
        if type(constant['default_value']) is not list and constant['_external']:
            constant_value = constants[constant_key]
            for node in nodes:
                if node['constants'][header['data_field']][constant_key] != constant_value:
                    constant_value = 'Multiple'
                    break

            multiple_allowed = True
            for node in nodes:
                multiple_allowed &= header.enables(node, 'const_set')

            output.append(
                bottle.template(
                    'constants_js',
                    constant=constant,
                    value=constant_value,
                    multiple_allowed=multiple_allowed
                )
            )

    # LOGGER.debug('constants_js_validation Time: ' + str(time.time() - start_time) + ' seconds')

    return output


def _constants_html(header, nodes):
    """
    Generate web interface html for the constants of a particular node

    :param nodes: list of nodes that we are working with
    :return: html string
    """
    # start_time = time.time()

    output = []
    constants = nodes[0]['constants'][header['data_field']]

    for constant_key, constant in header.constants.items():
        if constant['_external']:
            constant_value = constants[constant_key]
            for node in nodes:
                if node['constants'][header['data_field']][constant_key] != constant_value:
                    constant_value = 'Multiple'
                    break

            output.append(
                bottle.template(
                    'constants_html',
                    constant=constant,
                    value=constant_value
                )
            )

    output = '\n'.join(output)

    # LOGGER.debug('constants_html Time: ' + str(time.time() - start_time) + ' seconds')

    return output


### CLASSES ###
class WebPlatforms(object):
    def __init__(self, manager):
        self._manager = manager
        self._default_group = None
        self._warnings_state = 0

        self.validation_string = GROUP_VALIDATION

        ## Overloading Methods ##
        self.select_nodes = self._manager.platforms.select_nodes
        self.delete_node = self._manager.platforms.delete_node
        self.save = self._manager.platforms.save

    ## Cookie Methods ##
    def default_cookie(self, page_type):
        cookie = {'platforms': {}}

        if page_type in ('live', 'log'):
            _cookie = {}
            for platform_name, platform in self.items():
                _cookie[platform_name] = {}

                for group_name, group in platform.groups.items():
                    _cookie[platform_name][group_name] = group.default_cookie(page_type)

            cookie['platforms'] = _cookie

        else:
            LOGGER.error("Page type: " + str(page_type) + " does not exist!")

        return cookie

    ## Some Generic Web Methods ##
    def active_platforms(self):
        """ Returns active platforms """
        active_platforms = OrderedDict()
        for platform_name, platform in self.items():
            if len(platform.groups) > 1 or len(platform.groups.values()[0].nodes) > 0:
                active_platforms[platform_name] = platform

        return active_platforms

    def platform(self, address):
        """ Returns platform using address provided """
        output = None

        if 'platform' in address:
            output = self[address['platform']]

        return output

    def group(self, address):
        """ Returns group using address provided """
        output = None

        if 'group' in address:
            output = self.platform(address).groups[address['group']]

        return output

    def node(self, address, net_addr=None):
        """ Returns node using address provided """
        output = None

        if net_addr is None:
            if 'nodes' in address:
                if len(address['nodes']):
                    net_addr = address['nodes'][0]

        if net_addr is not None:
            output = self.group(address).nodes[net_addr]

        return output

    # FIXME: platforms.nodes() and group.nodes creates confusion!!!
    def nodes(self, address):
        """ Returns list of nodes using address provided """
        output = list()

        if 'nodes' in address:
            for net_addr in address['nodes']:
                node = self.node(address, net_addr)
                if node is not None:
                    output.append(node)

        return output

    ## Web Page Methods ##
    # URL Creation and Parsing #
    def compose_group_urls(self):
        """ Returns list of url and titles """
        sub_pages_list = []

        active_platforms = self.active_platforms()
        for platform_name, platform in active_platforms.items():
            for group_name, group in platform.groups.items():
                # Exclude inactive group
                if group_name != platform.groups.keys()[0]:
                    page_number = math.ceil(len(group.nodes) / float(LIVE_NODES_NUMBER))

                    page = 0
                    while page_number > page:
                        url = []
                        title = []

                        # Platform Part of the URL #
                        url.append(_url_encode(platform_name))
                        if len(active_platforms) > 1:
                            title.append(platform['name'])

                        # Group Part of the URL #
                        url.append(_url_encode(group_name))
                        if len(platform.groups) > 1:
                            title.append(group['name'])

                        # Page Part of the URL #
                        url.append(str(page + 1))
                        if page_number > 1:
                            title.append(PAGE + str(page + 1))

                        # Create url and title
                        sub_pages_list.append({'url': '-'.join(url), 'title': ' - '.join(title)})

                        page += 1

        if len(sub_pages_list) == 1:
            self._default_group = self.fetch_group_from_url(sub_pages_list[0]['url'])
        else:
            self._default_group = None

        return sub_pages_list

    def fetch_group_from_url(self, group_url):
        """ Returns group using url provided """
        target_group = self.values()[0].groups.values()[0]

        if group_url is not None:
            platform, group, page_number = _parse_url(group_url)
            if platform is not None:
                if group in self[platform].groups:
                    group = self[platform].groups[group]
                    nodes = group.nodes

                    # Calculate range for the nodes in the group
                    start = (page_number - 1) * LIVE_NODES_NUMBER
                    end = page_number * LIVE_NODES_NUMBER
                    if end > len(nodes):
                        end = len(nodes)

                    # LOGGER.debug("start = " + str(start))
                    # LOGGER.debug("end = " + str(end))

                    target_group = copy.copy(group)
                    target_group.nodes = OrderedDict()

                    for index in range(start, end):
                        target_group.nodes[nodes.keys()[index]] = nodes.values()[index]

                    # target_group.nodes = nodes[start:end]
                    # LOGGER.debug("len(target_group) = " + str(len(target_group)))

        elif self._default_group is not None:
            target_group = self._default_group

        return target_group

    ## Web Handler Methods ##
    # Some Generic Handler Methods #
    def parse_address(self, address):
        """ Prepare some values """
        target = None
        target_key = None
        target_index = None

        if 'platform' in address and address['platform'] is not None:
            target = self
            target_key = address['platform']
            target_index = target.keys().index(address['platform'])
            if 'group' in address and address['group'] is not None:
                target = self.platform(address).groups
                target_key = address['group']
                target_index = target.keys().index(address['group'])
                if 'nodes' in address and len(address['nodes']):
                    target = self.group(address).nodes
                    target_key = node = address['nodes'][0]
                    target_index = target.keys().index(node)

        return target, target_key, target_index

    def move_nodes(self, new_group_key, address):
        """ Move nodes from one group to another """
        new_address = address

        if new_group_key != address['group'] and new_group_key in self[address['platform']].groups:
            for net_addr in address['nodes']:
                update_snmp_settings = False
                node = self.node(address, net_addr)
                # Change inactive status if needed
                inactive_group_key = self[address['platform']].groups.keys()[0]
                if new_group_key == inactive_group_key:
                    node['inactive'] = True
                    update_snmp_settings = True
                elif address['group'] == inactive_group_key:
                    if node['modbus_addr'] is None:
                        node['modbus_addr'] = self._manager.nodes.modbus_address()
                    node['inactive'] = False
                    update_snmp_settings = True

                node['group'] = new_group_key

                # Update SNMP Settings (only when moving from or to inactive group)
                if update_snmp_settings:
                    new_group = self[address['platform']].groups[new_group_key]
                    node.error.update(copy.copy(new_group.error))

                # Move node
                del self[address['platform']].groups[address['group']].nodes[net_addr]
                self[address['platform']].groups[new_group_key].nodes[net_addr] = node

            # Cookie keeps the group
            new_address = self.update_address(address)

            # Cookie follows the node
            # new_address['group'] = new_group_key

        return new_address

    ## Address Related Methods ##
    def update_address(self, address):
        """ Sets cookie after moving or deleting node """
        new_address = address

        if 'platform' in address and 'group' in address and 'nodes' in address:
            if len(self[address['platform']].groups[address['group']].nodes):
                del new_address['nodes'][:]
            else:
                del new_address['nodes']

            # LOGGER.debug("new address = " + str(address))

        return new_address

    def flush_nodes(self, address):
        """ Flushes nodes from address if needed """
        new_address = address

        if 'nodes' in address:
            nodes = self.select_nodes('ALL')
            for net_addr in address['nodes']:
                if net_addr not in nodes.keys():
                    new_address = self.update_address(address)
                    break

        return new_address

    ## Warnings Methods ##
    def warnings(self):
        """ Returns list of warnings and the state of warnings """
        unacknowledged_acks = False
        new_warning = False

        # Gather warning providers
        nodes = self.select_nodes('all')
        base_node = self._manager.bridge.base
        statistics = self._manager
        warning_providers = nodes.values() + [base_node, statistics]

        # Merge all warnings
        _warnings = dict()
        for provider in warning_providers:
            provider_id = internal_name(provider['name'])
            if 'net_addr' in provider and provider['net_addr'] is not None:
                provider_id = provider['net_addr']
            _warnings.update(provider.error.get_error_messages(provider_id))

        # Create dictionary of warnings in reverse chronological order
        warnings = list()
        for warning_time in sorted(_warnings.keys())[::-1]:
            warning = _warnings[warning_time]
            warnings.append(warning)
            unacknowledged_acks |= warning['ack']
            new_warning |= warning['new']

        self._warnings_state = int(bool(len(warnings))) + int(bool(unacknowledged_acks)) + int(bool(new_warning))

        return warnings

    def warnings_state(self):
        """ Returns warnings state """
        return self._warnings_state

    ## SNMP Methods ##
    def update_snmp_dict(self, snmp_type, old_snmp_key, new_snmp_key):
        """ Updates SNMP keys in all dictionaries """
        targets = list()

        active_platforms = self.active_platforms()
        for platform in active_platforms.values():
            targets.append(platform)
            for group_name, group in platform.groups.items():
                if group_name != 'inactive_group':
                    targets.append(group)
                    for node in group.nodes.values():
                        targets.append(node)

        for target in targets:
            target.error.update_snmp_dict(snmp_type, old_snmp_key, new_snmp_key)
            target.error.save()

    ## Web Template Methods ##
    # Headers #
    def headers_html(self, address):
        """
        Generates headers table html using provided address
        :param address:
        :return:
        """
        output = ''

        group = self.group(address)
        nodes = self.nodes(address)

        if len(nodes):
            all_headers = group.read_headers('all', nodes)
            # diagnostics_headers = group.read_headers('diagnostics', nodes)

            # LOGGER.debug('all_headers: {}'.format(all_headers))

            header_table_content = ''
            for header_key, header in all_headers.items():
                # hide_header = bool(header_key in diagnostics_headers.keys())
                header_group = group.header_group(header_key, nodes)
                header_name = _header_select_html(header, header_group)
                header_html = _header_html(header, nodes)
                header_table_content += bottle.template(
                    'header_row_html',
                    hide_header=False,
                    # hide_header=hide_header,
                    header_name=header_name,
                    header_html=header_html,
                )

            output = bottle.template('header_table_html', header_table_content=header_table_content)

        return output

    # Constants #
    def constants_js_html(self, address):
        """ Generates constants js that validates constants """
        constants_js, constants_html = '', ''

        nodes = self.nodes(address)
        if len(nodes):
            js_validation_list = list()

            group = self.group(address)
            all_headers = group.read_headers('all', nodes)

            for header in all_headers.values():
                if header.external_constants():
                    js_validation_list += _constants_js(header, nodes)

            constants_js = 'else '.join(js_validation_list)

            constants_html = ''
            for header in all_headers.values():
                if header.external_constants():
                    header_html = _constants_html(header, nodes)
                    constants_html += bottle.template(
                        'constants_row_html',
                        header_name=header['name'],
                        header_html=header_html,
                    )

        return constants_js, constants_html

    ## Generic Macros ##
    def __iter__(self):
        return iter(self._manager.platforms)

    def __getitem__(self, key):
        """ Allows using self[key] method """
        return self._manager.platforms[key]

    def __setitem__(self, key, value):
        """ Allows using self[key] = value method """
        self._manager.platforms[key] = value

    def __delitem__(self, key):
        """ Allows using del self[key] method """
        del self._manager.platforms[key]

    def __len__(self):
        """ Allows using len(self) method """
        return len(self._manager.platforms)

    def __repr__(self):
        """ Allows using self method. Returns list of dictionaries """
        return repr(self._manager.platforms)

    def __str__(self):
        """ Allows using print self method """
        return str(self.__repr__())

    def items(self):
        """ Allows using items method """
        return self._manager.platforms.items()

    def values(self):
        """ Allows using values method """
        return self._manager.platforms.values()

    def keys(self):
        """ Allows using keys method """
        return self._manager.platforms.keys()
