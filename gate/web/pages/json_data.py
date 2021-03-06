"""
Everything related to generating JSON data
"""

### INCLUDES ###
import os
import copy
import logging

from bottle import template

from py_knife.file_system import remove_file
from py_knife.pickle import unpickle_file

from gate import strings
from gate.common import SNMP_RESPONSES_PATH
from gate.conversions import internal_name

from .status_icons import StatusIcons


### CONSTANTS ###
## Logs Plot Options Defaults ##
LOG_OPTIONS_DEFAULTS = {
    'zoom': {'interactive': True},
    'pan': {'interactive': True},
    'xaxes': [
        {
            #'show': False,
            'mode': 'time',
            'timeformat': '%H:%M'
        }
    ],
    'yaxes': []
}

YAXES_DEFAULTS = {
    'min': 0,
    'max': 100,
    'zoomRange': [1, 100],
    'panRange': [0, 100]
}

## Floating Switch States ##
SWITCH_STATES = {
    False: 'Switch is Open!',
    True: 'Switch is Closed!'
}

## Strings ##
PLEASE_SET = 'Please set '
CONSTANTS = 'sensor parameters '
DISPLAY_ENABLES = 'display enables '
TRACK_ENABLES = 'track enables '
TO_DISPLAY1 = 'in order to display '
TO_DISPLAY2 = 'data!'

LOG_MEASURING = " log measuring "
NO_LOG = " data is empty!"

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class PagesJsonData(StatusIcons):
    """
    JSON Data Mixin. Used by pages class.
    This methods are used by pages to return json data for live and logs pages via web forms.
    The returned JSON data is mainly used to draw bar graphs and charts using Flot drafting engine
    based on jquery and javascript
    """

    def __init__(self, **kwargs):
        super(PagesJsonData, self).__init__(**kwargs)

        ## Initialize Forms ##
        self._forms = [
            # Page Specific Forms #
            # Live Data Form
            {
                'template': os.path.join(os.path.join(*self.url('live_data').split('/')), 'table'),
                'get_handler': (self.__live_table, 'read')
            },
            # Logs Data Form
            {
                'template': os.path.join(os.path.join(*self.url('logs_data').split('/')), 'table'),
                'get_handler': (self.__logs_table, 'read')
            },
            # Field Unit Update Form
            {
                'template': os.path.join(os.path.join(*self.url('nodes_subpage').split('/')), 'field_unit_update'),
                'get_handler': (None, 'read')
            },
            # Sensor Parameters Form
            {
                'template': os.path.join(os.path.join(*self.url('nodes_subpage').split('/')), 'sensor_parameters'),
                'get_handler': (None, 'read')
            },
            # Generic Forms(across multiple pages) #
            # User/Group/Agent/Command Validation Form
            {
                'template': 'name_validation',
                'get_handler': (self.__name_validation, 'user')
            },
            # Software Form
            {
                'template': 'software_update',
                'get_handler': (None, 'user')
            },
            # Ack Update
            {
                'template': 'ack_update',
                'get_handler': (self.__ack_update, 'read')
            },
        ]

    ## Private Methods ##
    # JSON #
    def _json_for_ajax_update(self):
        """ Creates JSON dictionary for AJAX update """
        json_dict = dict()

        json_dict.update(self._status_icons_json())

        if self.manager.system_settings.snmp_enable:
            json_dict.update(self.__get_snmp_responses())

        return json_dict

    ## Class-Private Methods ##
    # LiveData #
    def __live_table(self, group_url=None):
        """ Generate json for both table and form """
        group = self.platforms.fetch_group_from_url(group_url)

        json_dict = {
            'page_controls': template('page_controls', group=group, page_type='live'),
            'table': self.template_html('live_data', 'table', group=group),
            'form': self.__live_form(group)
        }
        return json_dict

    # Logs #
    def __logs_table(self, group_url=None):
        """ Generate json for both table and form """
        group = self.platforms.fetch_group_from_url(group_url)

        json_dict = {
            'table': self.template_html('logs_data', 'table', group=group),
            'form': self.__logs_form(group)
        }

        return json_dict

    # Validation Method #
    def __name_validation(self, **kwargs):
        """ Validate provided username or group name """
        output = {}

        cookie = self.get_cookie()
        if type(cookie) is dict and 'index' in cookie:
            address = cookie['index']
        else:
            address = cookie

        handler_tuple = self._parse('post_handler')
        if handler_tuple is not None:
            post_handler = handler_tuple[0]

            output = post_handler.name_validation(address, **kwargs)

        return output

    # Warning Ack Update #
    def __ack_update(self, warning_key, ack_value):
        """ Update warning acknowledgements """
        json_dict = dict()

        warning_key_list = warning_key.split('-')
        if len(warning_key_list) == 3:
            provider_id = warning_key_list[0]
            error_field = warning_key_list[1]
            error_code = int(warning_key_list[2])

            statistics = {internal_name(self.manager['name']): self.manager}
            active_nodes = self.platforms.select_nodes('active')
            providers = statistics
            providers.update(active_nodes)
            if provider_id in providers:
                provider = providers[provider_id]
                ack_value = not bool(int(ack_value))
                provider.error.change_ack_state(error_field, error_code, ack_value)

                json_dict.update(self._json_for_ajax_update())

            else:
                # Can not locate node referenced by warning key
                json_dict['alert'] = strings.NO_NODE

        else:
            # Unrecognized warning key
            json_dict['alert'] = strings.UNKNOWN_ERROR

        return json_dict

    def __live_form(self, group):
        """ Generate json for Live Data page """
        json_dict = {'nodes': []}
        json_dict.update(self.__get_warnings(group))

        if len(group.nodes):
            cookie = self.get_cookie()

            group_header = group.live_header(cookie)
            # LOGGER.debug('')
            # LOGGER.debug('group_header: {}'.format(group_header['name']))

            for net_addr, node in group.nodes.items():
                # LOGGER.debug('node: {}'.format(node['name']))
                if group_header is not None:
                    node_json = {'name': node['name']}

                    # Data Entry Hack for 'Multiple' Headers #
                    live_header = None
                    if 'multiple' in group_header['internal_name']:
                        live_headers = group.live_headers([node]).values()
                        # live_headers = node.read_headers('display')

                        header_position = group_header['header_position']
                        if header_position < len(live_headers):
                            live_header = live_headers[header_position]

                    if live_header is None:
                        live_header = group_header

                    # LOGGER.debug('live_header: {}'.format(live_header['name']))

                    live_units = node.live_units(cookie, live_header)
                    # LOGGER.debug('live_units: {}'.format(live_units['name']))

                    # Warning #
                    warning = ''
                    bar_graph_enable = True
                    if not live_header.enables(node, 'const_set'):
                        warning += PLEASE_SET + node['name'] + ' ' + CONSTANTS
                        warning += TO_DISPLAY1 + live_header['name'] + ' ' + TO_DISPLAY2
                    elif not live_header.enables(node, 'live_enables'):
                        warning += PLEASE_SET + live_header['name'] + ' ' + DISPLAY_ENABLES
                        warning += TO_DISPLAY1 + live_header['name'] + ' ' + TO_DISPLAY2
                    else:
                        switch_state = None
                        if live_units['internal_name'] in ('floating_switch', 'switch'):
                            _switch_state = bool(live_units.get_float(node))
                            switch_state = SWITCH_STATES[_switch_state]

                        node_fault = node.error.node_fault()
                        sensor_fault = node.error.sensor_fault(live_header)

                        for potential_warning in (switch_state, node_fault, sensor_fault):
                            if potential_warning is not None:
                                bar_graph_enable = False
                                warning += potential_warning
                                break

                    node_json['warning'] = warning

                    # Bar Graph Data #
                    current_value = live_units.get_string(node)
                    # LOGGER.debug('current_value: {}'.format(current_value))

                    bar_graph_enable &= bool(current_value is not None)

                    if bar_graph_enable:
                        # LOGGER.debug('node: '.format(net_addr))

                        min_value = live_units.get_min(node)
                        max_value = live_units.get_max(node)

                        # Series #
                        series_dict = {'data': [[0, current_value, min_value]]}

                        if not node['presence']:
                            series_dict['color'] = 'yellow'
                        else:
                            alarm_triggered = node.error.alarm_triggered(live_header)
                            # LOGGER.debug('alarm_triggered: {}'.format(alarm_triggered))

                            if alarm_triggered:
                                series_dict['color'] = 'red'
                            else:
                                series_dict['color'] = 'green'

                        # series_dict['label'] = live_header['name']
                        node_json['series'] = [series_dict]

                        # Options #
                        node_json['options'] = {
                            'series': {
                                'bars': {
                                    'show': True,
                                    'barWidth': 0.25,
                                    'align': 'center'
                                }
                            },
                            'grid': {
                                'hoverable': True,
                                'clickable': True
                            },
                            'legend': {
                                'position': 'se'
                            },
                            'xaxis': {
                                # 'position': 'top',
                                'min': -0.5,
                                'max': 0.5,
                                # 'ticks': [[0, node['name']]],
                                'ticks': [[0, '']],
                                'tickLength': 0
                            },
                            'yaxis': {
                                'min': min_value,
                                'max': max_value
                            }
                        }

                        # Presence #
                        # node_json['presence'] = int(node['presence'])

                    # Node Data #
                    node_json['data'] = {}
                    group_headers = group.read_headers('display')
                    node_headers = node.read_headers('display').values()
                    for _group_header_name, _group_header in group_headers.items():
                        group_log_units = group.log_table_units(cookie, _group_header)

                        _group_header_position = _group_header['header_position']
                        if _group_header_position < len(node_headers):
                            node_header = node_headers[_group_header_position]
                            node_log_units = node.log_table_units(cookie, node_header)
                            for unit_index, group_log_unit_name in enumerate(group_log_units.keys()):
                                data_name = _group_header_name + '_' + group_log_unit_name

                                node_log_unit = node_log_units.values()[unit_index]
                                current_value = node_log_unit.get_string(node)
                                node_json['data'][data_name] = current_value

                    json_dict['nodes'].append(node_json)

        return json_dict

    def __logs_form(self, group):
        """ Generate json for Logs Data page """
        logs_data = self.__get_logs_data(group)

        json_dict = {'series': [], 'options': copy.deepcopy(LOG_OPTIONS_DEFAULTS)}
        json_dict.update(self.__get_warnings(group, logs_data))

        cookie = self.get_cookie()

        # Initialised for options below
        min_time = self.manager.system_settings.log_time()
        max_time = 0

        # Series #
        for entry in logs_data:
            node_index = entry['node_index']
            header_index = entry['header_index']
            header = entry['header']
            node = entry['node']
            logs = entry['logs']

            if len(logs):
                # Updated for options below
                test_min_time = self.manager.system_settings.log_time(logs[0]['time'])
                test_max_time = self.manager.system_settings.log_time(logs[-1]['time'])
                if test_min_time < min_time:
                    min_time = test_min_time
                if test_max_time > max_time:
                    max_time = test_max_time

                color_number = node_index * len(node.read_headers('display')) + header_index
                json_dict['series'].append({'color': color_number})

                json_dict['series'][-1]['label'] = node['name'] + " " + header['name']
                # json_dict['series'][-1]['yaxis'] = len(json_dict['series'])
                json_dict['series'][-1]['data'] = []

                log_units = node.log_units(cookie, header)
                if cookie['single_point']:
                    # LOGGER.debug('Single Point!')
                    current_time = self.manager.system_settings.log_time(logs[-1]['time'])
                    current_value = log_units.get_string(node, logs[-1])
                    json_dict['series'][-1]['data'].append([current_time, current_value])
                else:
                    for log_entry in logs:
                        log_time = self.manager.system_settings.log_time(log_entry['time'])
                        log_value = log_units.get_string(node, log_entry)
                        json_dict['series'][-1]['data'].append([log_time, log_value])

        # Options #
        # Make sure we have logs to display (use defaults otherwise)
        if len(json_dict['series']):
            json_dict['options']['series'] = {
                'lines': {'show': True},
                'points': {'show': True}}
            json_dict['options']['grid'] = {'hoverable': True}
            # json_dict['options']['legend'] = {'position': 'se'}
            json_dict['options']['xaxes'][0]['zoomRange'] = [60000, int(max_time)]
            json_dict['options']['xaxes'][0]['panRange'] = [int(min_time), int(max_time)]

            for index, entry in enumerate(logs_data):
                header = entry['header']
                node = entry['node']
                logs = entry['logs']

                if len(logs):
                    # Get min and max values while considering Output Options
                    log_units = node.log_units(cookie, header)
                    min_value = log_units.get_min(node)
                    max_value = log_units.get_max(node)

                    yaxes = {
                        'min': min_value,
                        'max': max_value,
                        'zoomRange': [5, max_value],
                        'panRange': [0, max_value]
                    }

                    # Combine yaxes if possible
                    if not (yaxes in json_dict['options']['yaxes']):
                        json_dict['options']['yaxes'].append(yaxes)

                    json_dict['series'][index]['yaxis'] = json_dict['options']['yaxes'].index(yaxes) + 1

        else:
            json_dict['series'].append({})
            json_dict['options']['yaxes'].append(YAXES_DEFAULTS)

        return json_dict

    def __get_logs_data(self, group):
        """ Generate data for logs """
        logs_data = []

        cookie = self.get_cookie()
        selected_headers = group.log_header(cookie)
        for net_addr, node in group.nodes.items():
            if net_addr in selected_headers:
                node_headers = selected_headers[net_addr]
                # LOGGER.debug('node_headers[{}]: {}'.format(net_addr, node_headers))

                display_headers = node.read_headers('display')
                for header_index, header in enumerate(display_headers.values()):
                    if header['internal_name'] in node_headers.keys():
                        node_index = group.nodes.keys().index(net_addr)
                        logs_data.append({
                            'node_index': node_index,
                            'header_index': header_index,
                            'header': header,
                            'node': node,
                            'logs': []
                        })
                        if header.enables(node, 'log_enables') and header.enables(node, 'const_set'):
                            logs_data[-1]['logs'] = [log for log in node.logs[-self.manager.system_settings['log_limit']:]
                                                     if log[header['data_field']] is not None]

        # LOGGER.debug('logs_data: {}'.format(logs_data))
        return logs_data

    def __get_warnings(self, group, logs_data=None):
        """ Generates all warnings (if any) for particular node. Returns warnings list """
        json_dict = dict()
        display_warnings = list()

        if not len(self.platforms.select_nodes('active')):
            display_warnings.append(strings.NO_ACTIVE_NODES)

        else:
            page_type = 'live'
            if logs_data:
                page_type = 'log'

            enabled_headers = getattr(group, page_type + '_headers')()
            if len(enabled_headers) == 0:
                if logs_data is None:
                    display_warnings.append(PLEASE_SET + DISPLAY_ENABLES + TO_DISPLAY1 + TO_DISPLAY2)
                else:
                    display_warnings.append(PLEASE_SET + TRACK_ENABLES + TO_DISPLAY1 + TO_DISPLAY2)

            if logs_data:
                for entry in logs_data:
                    header = entry['header']
                    node = entry['node']
                    logs = entry['logs']

                    if not header.enables(node, 'const_set'):
                        display_warnings.append(PLEASE_SET + node['name'] + ' ' + CONSTANTS +
                                                TO_DISPLAY1 + header['name'] + ' ' + TO_DISPLAY2)
                    elif not len(logs):
                        display_warnings.append(node['name'] + LOG_MEASURING + header['name'] + NO_LOG)

        if len(display_warnings):
            json_dict['display_warnings'] = '\n'.join(display_warnings)

        return json_dict

    def __get_snmp_responses(self):
        """ Fetches SNMP responses (and alerts user if needed) """
        json_dict = dict()

        # Load snmp_response file
        snmp_response = unpickle_file(SNMP_RESPONSES_PATH)
        if snmp_response is not False:
            # If on snmp_agents or snmp_command page prompt success
            # LOGGER.debug('SNMP Response: {}'.format(snmp_response))
            if snmp_response is not None:
                page_url = self.url()
                if self.url('snmp_agents') in page_url or self.url('snmp_commands') in page_url:
                    json_dict['alert'] = strings.TEST_SUCCESS1 + str(snmp_response) + strings.TEST_SUCCESS2
            # Else prompt only failure
            else:
                json_dict['alert'] = strings.TEST_FAILURE

            # Delete snmp_response file
            remove_file(SNMP_RESPONSES_PATH)

        return json_dict
