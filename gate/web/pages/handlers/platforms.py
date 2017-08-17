"""
Platforms Web Handler with integrated Edit Methods
"""

### INCLUDES ###
import os
import time
import copy
import json
import logging

from bottle import request, static_file
# from tornado import ioloop, gen

from py_knife import file_system, pickle

from gate import strings
from gate.common import UPLOADS_FOLDER, LOGS_FOLDER
from gate.conversions import internal_name
from gate.update_interface import WorkerThread
from gate.sleepy_mesh.platforms import Platform, Group

from gate.web.pages.handlers import WebHandlerBase


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class WebHandler(WebHandlerBase):
    """ This a functionality for edit methods aka web methods """
    def __init__(self, pages):
        super(WebHandler, self).__init__(pages, pages.platforms)
        self._log_export = None

    # Generic #
    def _up(self, address):
        """ Move addressed value up """
        target, target_key, target_index = self._object.parse_address(address)
        validate = target_index > 0

        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if validate:
            # Up actually decrements index
            insert_key = target.keys()[target_index - 1]
            target_value = target.pop(target_key)
            target.insert_before(insert_key, (target_key, target_value))

            self._object.save()
        else:
            return_dict['kwargs']['alert'] = strings.VALIDATION_FAIL

        return return_dict

    def _down(self, address):
        """ Move addressed value down """
        target, target_key, target_index = self._object.parse_address(address)
        validate = target_index < (len(target) - 1)

        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if validate:
            # Down actually increments index
            insert_key = target.keys()[target_index + 1]
            target_value = target.pop(target_key)
            target.insert_after(insert_key, (target_key, target_value))

            self._object.save()
        else:
            return_dict['kwargs']['alert'] = strings.VALIDATION_FAIL

        return return_dict

    def _remove(self, address):
        """ Remove addressed value """
        target, target_key, target_index = self._object.parse_address(address)
        validate = target_index < len(target)
        new_address = address

        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if validate:
            if 'nodes' in address and target_key:
                # Move to inactive
                inactive_group = self._object[address['platform']].groups.keys()[0]
                if address['group'] != inactive_group:
                    # Move to inactive group
                    # LOGGER.debug("Move node to inactive group!")
                    return_dict['new_cookie'] = self._object.move_nodes(inactive_group, address)
                else:
                    # Remove
                    # LOGGER.debug("Remove node!")
                    for node in self._object.nodes(address):
                        # del target[node['net_addr']]
                        node.delete()
                        self._object.delete_node(node)
                        return_dict['new_cookie'] = self._object.update_address(address)

                return_dict['save_cookie'] = True

            elif 'group' in address and target_key == address['group']:
                if len(target) > 1:
                    # Remove
                    target_nodes = target[target_key].nodes

                    for node in target_nodes.values():
                        node['inactive'] = True
                    target.values()[0].nodes.update(target_nodes)

                    target[target_key].delete()
                    del target[target_key]

                else:
                    # Restore to default
                    group_nodes = target[target_key].nodes
                    for net_addr, node in group_nodes.items():
                        node['inactive'] = True

                    target[target_key].delete()
                    del target[target_key]

                    group_value = Group('Inactive Group', self._manager.nodes, target.headers)
                    group_key = group_value['internal_name']
                    target[group_key] = group_value
                    target[group_key].nodes = group_nodes

                return_dict['save_cookie'] = True
                new_address['group'] = self._object[address['platform']].groups.keys()[0]
                return_dict['new_cookie'] = new_address

            elif 'platform' in address and target_key == address['platform']:
                # Restore to default
                groups = target[target_key].groups.values()
                for group in groups:
                    for net_addr, node in group.nodes.items():
                        node['inactive'] = True
                        groups[0].nodes[net_addr] = node

                platform_nodes = copy.copy(groups[0].nodes)

                target[target_key].delete()
                del target[target_key]

                target[target_key] = Platform(target_key, self._manager.nodes)
                target[target_key].groups.values()[0].nodes = platform_nodes

            self._object.save()
        else:
            return_dict['kwargs']['alert'] = strings.VALIDATION_FAIL

        return return_dict

    def _restore(self, address):
        """ Restore addressed value """
        return self._remove(address)

    # Platforms #
    def _update_platform(self, address):
        """ Updates platform variables (platform_name) """
        platform_name = request.forms.platform_name.encode('ascii', 'ignore')
        validate = len(platform_name) > 0

        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if validate:
            self._object.platform(address).update({'name': platform_name})

            self._object.save()
        else:
            return_dict['kwargs']['alert'] = strings.VALIDATION_FAIL

        return return_dict

    # Groups #
    def _create_group(self, address):
        """ Creates new group """
        group_name = request.forms.group_name.encode('ascii', 'ignore')
        validate = len(group_name) > 0 and not (self.name_taken(address, group_name))
        new_address = address

        return_dict = {
            'kwargs': {},
            'save_cookie': validate
        }

        if validate:
            platform = self._object.platform(address)

            new_group = Group(group_name, self._manager.nodes, platform.headers)
            group_key = new_group['internal_name']
            # Copy node defaults from platform
            new_group.error.update(copy.deepcopy(platform.error))
            platform.groups[group_key] = new_group

            new_address['group'] = group_key

            return_dict['new_cookie'] = new_address
            self._object.save()
        else:
            return_dict['kwargs']['alert'] = strings.VALIDATION_FAIL

        return return_dict

    def _update_group(self, address):
        """ Updates group (group_name) and associated group key """
        group_name = request.forms.group_name.encode('ascii', 'ignore')
        validate = len(group_name) > 0 and not (self.name_taken(address, group_name))
        new_address = address

        return_dict = {
            'kwargs': {},
            'save_cookie': validate
        }

        if validate:
            group = self._object.group(address)
            groups = self._object.platform(address).groups
            index = groups.values().index(group)

            group_value = Group(group_name, self._manager.nodes, group.headers)
            group_value.nodes = group.nodes
            group_key = group_value['internal_name']

            group.delete()
            del groups[group['internal_name']]

            if index < len(groups):
                groups.insert_before(groups.keys()[index], (group_key, group_value))
            else:
                groups[group_key] = group_value

            new_address['group'] = group_key

            return_dict['new_cookie'] = new_address
            self._object.save()
        else:
            return_dict['kwargs']['alert'] = strings.VALIDATION_FAIL

        return return_dict

    # Nodes #
    def _update_node(self, address):
        """ Updates node variables """
        return_dict = {'kwargs': {}}

        if 'nodes' in address and len(address['nodes']):
            validate = True
            save_dict = dict()
            update_node = bool(request.forms.node_name)
            update_network = bool(request.forms.channel)
            update_enables = bool(request.forms.total_display)
            update_enables &= bool(request.forms.total_track)
            update_enables &= bool(request.forms.total_diagnostics)

            if update_node:
                save_dict.update({
                    'name': request.forms.node_name.encode('ascii', 'ignore'),
                    'sensor_type': request.forms.sensor_type.encode('ascii', 'ignore')
                    # 'mac': request.forms.mac_str.encode('ascii', 'ignore')
                })

                # Validate data
                # Make sure values are not empty
                for value in save_dict.values():
                    validate &= 0 < len(value) < 255

                # # Make sure MAC is 16 bytes and has valid digits
                # validate &= all(char in string.hexdigits for char in save_dict['mac']) \
                #             and (len(save_dict['mac']) == 16)

                # Modbus Address
                modbus_addr = request.forms.get('modbus_addr')
                if modbus_addr:
                    modbus_addr = int(modbus_addr)
                    node = self._object.node(address)
                    validate &= (modbus_addr not in self._manager.nodes.modbus_addresses() or
                                 modbus_addr == node['modbus_addr'])
                    if validate:
                        node['modbus_addr'] = modbus_addr

                # Alarms
                platform = self._object.platform(address)
                all_headers = platform.headers.read('all').values()
                for header in all_headers:
                    header_name = header['internal_name']
                    LOGGER.debug("header = " + header_name)
                    # Alarm Units
                    alarm_units = request.forms.get('alarm_units_' + header_name)
                    if alarm_units:
                        alarm_units = alarm_units.encode('ascii', 'ignore')
                        for node in self._object.nodes(address):
                            alarm_units = header.alarm_units(node, alarm_units)

                    for alarm_type in ('min_alarm', 'max_alarm'):
                        # Alarm Enables
                        alarm_enables = request.forms.get('total_' + alarm_type)
                        if alarm_enables:
                            alarm_enables = json.loads(alarm_enables.encode('ascii', 'ignore'))
                            if alarm_enables:
                                if header_name in alarm_enables:
                                    LOGGER.debug(alarm_type + '_enable = ' + str(alarm_enables[header_name]))
                                    for node in self._object.nodes(address):
                                        header.alarm_enable(node, alarm_type, alarm_enables[header_name])

                        # Alarm Values
                        alarm_value = request.forms.get(alarm_type + '_value_' + header_name)
                        if alarm_value:
                            LOGGER.debug(alarm_type + "_value = " + str(alarm_value))
                            alarm_value = float(alarm_value)

                            for node in self._object.nodes(address):
                                # Validate alarm values
                                low_limit = alarm_units.get_min(node)
                                high_limit = alarm_units.get_max(node)
                                validate &= low_limit is not None and high_limit is not None
                                if validate:
                                    validate &= (low_limit < alarm_value < high_limit)
                                    if validate:
                                        # Set alarm values
                                        header.alarm_value(node, alarm_type, alarm_value)
                                else:
                                    validate = False

            if update_network:
                save_dict['channel'] = int(request.forms.channel)
                save_dict['data_rate'] = int(request.forms.data_rate)
                save_dict['aes_enable'] = int(request.forms.aes_enable)

                # Make sure aes_key is 16 bytes long if enabled
                if save_dict['aes_enable'] == 1:
                    save_dict['aes_key'] = request.forms.aes_key.encode('ascii', 'ignore').ljust(16)
                    validate &= (len(save_dict['aes_key']) <= 16)

            return_dict['save_cookie'] = validate

            if validate:
                if update_enables:
                    display = json.loads(request.forms.total_display.encode('ascii', 'ignore'))
                    track = json.loads(request.forms.total_track.encode('ascii', 'ignore'))
                    diagnostics = json.loads(request.forms.total_diagnostics.encode('ascii', 'ignore'))

                    update_dict = dict()
                    if display and track and diagnostics:
                        platform = self._object.platform(address)
                        for node in self._object.nodes(address):
                            enables_map = {'live_enable': display, 'log_enable': track, 'diagnostics': diagnostics}
                            for enable_type, enable_dict in enables_map.items():
                                update_dict[enable_type] = platform.headers.update_enables(
                                    enable_type, node, enable_dict)

                    update_enables = bool(len(update_dict))
                    if update_enables:
                        update_dict['live_enable'] |= update_dict.pop('diagnostics')
                        save_dict.update(update_dict)

                    update_node |= update_enables

                nodes = self._object.nodes(address)

                if update_node or update_network:
                    self._manager.request_update(save_dict, nodes=nodes)

                # Change node group (if needed)
                new_group = request.forms.new_group.encode('ascii', 'ignore')
                return_dict['new_cookie'] = self._object.move_nodes(new_group, address)

                # Request preset update (if needed)
                if not update_enables:
                    self._manager.request_update(nodes=nodes)

                self._object.save()
            else:
                return_dict['kwargs']['alert'] = strings.VALIDATION_FAIL

        # Inactive node update triggers this page again which triggers this alert
        # else:
        #     return_dict['kwargs']['alert'] = NO_NODE

        return return_dict

    # Adc Constants #
    def _update_adc(self, address):
        """ Updates adc constants of the selected nodes """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if len(address['nodes']):
            validate = True

            # Create save dictionary
            save_dict = {}
            header_list = []

            # Iterate over all constants
            platform = self._object.platform(address)
            all_headers = platform.headers.read('all').values()
            for header in all_headers:
                if header.external_constants():
                    for constant_name, constant_value in header.constants.items():
                        if constant_value['_external']:
                            data_field = header['data_field']
                            constant_field_name = data_field + '_' + constant_name
                            value = request.forms.get(constant_field_name)
                            # Check if value was provided
                            if value:
                                # Convert to appropriate format
                                try:
                                    value = value.encode('ascii', 'ignore')
                                except:
                                    LOGGER.debug("Constant is in utf-8 encoding!")
                                else:
                                    value = value.encode('utf-8')

                                if value.split('.')[0].isdigit():
                                    value = float(value)

                                # Validate values
                                # Note: Options are not validated at the moment
                                if type(constant_value['default_value']) is not list:
                                    value = float(value)
                                    validate &= (constant_value['min_value'] <= value <= constant_value['max_value'])
                                elif value in ('True', 'False', u'True', u'False'):
                                    value = bool(value in ('True', u'True'))

                                if validate:
                                    # Append save_dict
                                    if data_field not in save_dict:
                                        save_dict[data_field] = dict()
                                    save_dict[data_field][constant_name] = value
                                    if constant_name != 'tank_type' and header not in header_list:
                                        header_list.append(header)

                                    # Update measuring units (if applicable)
                                    # TODO: Change to dynamic/common scheme of some sort...
                                    # TODO: Move to cookies
                                    if type(constant_value['default_value']) is list and constant_name == 'measuring_units':
                                        header.unit_list.values()[0]['measuring_units'] = value
                                        header.save()

                                else:
                                    break

                            elif constant_field_name not in ('adc0_area', 'adc0_diameter', 'adc0_length'):
                                print('Constant Field Name: {}'.format(constant_field_name))
                                print('Value: {}'.format(value))

                                # Do not allow multiple entry if one of the nodes does not have constants fully set
                                for node in self._object.nodes(address):
                                    validate &= header.enables(node, 'const_set')

                                    if not validate:
                                        break

                else:
                    # Just in case
                    header_list.append(header)

                if not validate:
                    break

            # Load local buffers with save dictionary
            if validate:
                # Set const_set flag
                for node in self._object.nodes(address):
                    for header in header_list:
                        header.enables(node, 'const_set', True)

                    # LOGGER.debug(header['name'] + ' const_set = ' + str(header.enables(node, 'const_set')))

                    # Update constants
                    for data_field, data_dict in save_dict.items():
                        node['constants'][data_field].update(data_dict)

                        # Inner dictionaries get lost this way...
                        # node['constants'].update(save_dict)

                self._object.save()
            else:
                return_dict['kwargs']['alert'] = strings.VALIDATION_FAIL
        else:
            return_dict['kwargs']['alert'] = strings.NO_NODE

        return return_dict

    # Logs #
    def _start_log_export(self, address):
        """ Starts exporting selected Log """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        net_addr = request.forms.net_addr.encode('ascii', 'ignore')
        active_nodes = self._manager.platforms.select_nodes('active')

        if net_addr in active_nodes:
            node = active_nodes[net_addr]

            if node.logs.not_empty():
                # LOGGER.debug('main niceness1 = ' + str(os.nice(0)))
                if self._log_export is not None:
                    self._log_export.stop()

                self._log_export = LogExportThread(self._manager, address, node)
                self._log_export.start()

                # LOGGER.debug('main niceness2 = ' + str(os.nice(0)))
            else:
                return_dict['alert'] = strings.LOG_EMPTY
        else:
            return_dict['alert'] = strings.NO_NODE

        return return_dict

    def _finish_log_export(self, address):
        """ Finishes Log Export by providing csv file """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        csv_name = file_system.fetch_file(os.path.join(UPLOADS_FOLDER, '*.csv'))

        if csv_name:
            return_dict['new_page'] = static_file(csv_name, root=UPLOADS_FOLDER, download=True)

            if self._log_export is not None:
                self._log_export.stop()
            self._log_export = None

        else:
            return_dict['kwargs']['alert'] = strings.UNKNOWN_ERROR

        return return_dict

    def _cancel_log_export(self, address):
        """ Cancels Log Export """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if self._log_export is not None:
            self._log_export.stop()
            self._log_export = None

        return return_dict

    def _remove_log(self, address):
        """ Removes selected Log """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        # net_addr = request.forms.net_addr.encode('ascii', 'ignore')
        net_addr = address['export_net_addr']

        active_nodes = self._object.select_nodes('active')
        if net_addr in active_nodes:
            node = active_nodes[net_addr]
            logs_are_present = node.logs.clear()

            if not logs_are_present:
                return_dict['kwargs']['alert'] = strings.LOG_ALREADY_EMPTY

        else:
            return_dict['kwargs']['alert'] = strings.NO_NODE

        return return_dict

    def _manual_log(self, address):
        """ Enable manual logging """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        net_addr = request.forms.net_addr.encode('ascii', 'ignore')
        # net_addr = address['export_net_addr']

        active_nodes = self._object.select_nodes('active')
        if net_addr in active_nodes:
            node = active_nodes[net_addr]
            node.logs.manual_log()
        else:
            return_dict['kwargs']['alert'] = strings.NO_NODE

        return return_dict

    def _save_software(self, address):
        """ Just a buffer """
        if 'nodes' not in address or not len(address['nodes']):
            return {'kwargs': {'alert': strings.NO_NODE}}

        else:
            nodes = self._object.nodes(address)
            return self._manager.uploader.init_upload(nodes[0]['type'], nodes)

    def _load_base_page(self, address):
        """ Loads base page """
        return_dict = {
            'kwargs': {},
            'save_cookie': True
        }

        active_platforms = self._object.active_platforms()

        if len(active_platforms) == 1:
            return_dict['new_cookie'] = {'platform': active_platforms.keys()[0]}
        else:
            return_dict['new_cookie'] = self._pages.default_cookie()

        return return_dict

    def name_taken(self, address, prospective_name):
        """ Checks if group_name is taken """
        group_key = internal_name(prospective_name)

        if 'group' in address:
            old_group_key = bool(group_key == address['group'])
        else:
            old_group_key = False

        group_key_taken = bool(group_key in self._object[address['platform']].groups)

        output = group_key_taken and not old_group_key
        return output


class LogExportThread(WorkerThread):
    """ Worker based on Thread class """
    def __init__(self, manager, cookie, node):
        super(LogExportThread, self).__init__()
        self._manager = manager
        self._update_interface = self._manager.update_interfaces.create(('log_export', ))
        self._cookie = cookie
        self._node = node

    def run(self):
        """ Creates CSV file """
        self.set_running(True)
        self._update_interface.start_update('log_export')

        # process_niceness = os.nice(SIDE_PROCESS_NICENESS)
        # LOGGER.debug('log export niceness = ' + str(process_niceness))

        # Yield so web page fetched first before processing this request
        time.sleep(0.5)
        # FIXME: Bellow method is for the schedule() method and not for the separate thread
        # yield gen.Task(ioloop.IOLoop.instance().add_timeout, time.time() + 0.5)

        csv_data = None
        current_file = 0.0

        if self.get_running():
            # Remove old files
            file_system.remove_files(os.path.join(UPLOADS_FOLDER, '*'))

        if self.get_running():
            # Building csv headers
            csv_data = 'Time'
            display_headers = self._node.headers.read('display').values()
            for header in display_headers:
                for log_unit in header.table_units(self._cookie, 'log').values():
                    csv_data += ',' + header['name'] + ' - ' + log_unit['measuring_units']

        # Dump stored files on HD
        if self.get_running() and csv_data is not None:
            files = self._node.logs.files()
            if len(files):
                for item_path in files:
                    current_file += 1.0
                    # LOGGER.debug("item_path = " + str(item_path))
                    item_name = os.path.basename(item_path)
                    logs = pickle.unpickle_file(os.path.join(LOGS_FOLDER, item_name))
                    if logs is not False:
                        _csv_data = self._append_csv(current_file, logs)
                        if _csv_data is not None:
                            csv_data += _csv_data
                        else:
                            csv_data = _csv_data

        # Dump current logs
        if self.get_running() and csv_data is not None:
            current_file += 1.0
            _csv_data = self._append_csv(current_file)
            if _csv_data is not None:
                csv_data += _csv_data
            else:
                csv_data = _csv_data

            # LOGGER.debug("CSV data: " + csv_data)

        message = 'Log Export'
        if self.get_running() and csv_data is not None:
            # Saving CSV file on HD under logs folder
            file_name = self._node.logs.name
            _csv_name = 'Log_' + file_name + '.csv'
            csv_name = file_system.save_file(os.path.join(UPLOADS_FOLDER, _csv_name), csv_data, 'utf-8-sig')

            if csv_name is None:
                message += strings.FAILED
            else:
                message += strings.COMPLETE
        else:
            message += strings.CANCELLED

        self._update_interface.finish_update(message)
        self.set_running(False)

    def _append_csv(self, current_log, points=None):
        """ Appends CSV string """
        csv_data = ''
        files = self._node.logs.files()
        # LOGGER.debug("files = " + str(files))
        total_logs = float(len(files) + 1.0)

        _progress_message = strings.PROCESSING + 'log {0:>3} out of {1:>3} logs, '.format(
            int(current_log), int(total_logs))

        if points is None:
            points = self._node.logs

        current_point = 0.0
        total_points = float(len(points))
        if total_points:
            display_headers = self._node.headers.read('display').values()
            for point in points:
                if self.get_running():
                    current_point += 1.0
                    progress_message = _progress_message
                    progress_message += 'point {0:>3} out of {1:>3} points!'.format(
                        int(current_point), int(total_points))

                    # Note: We substituting 1 from current point to signalize that we started working on this point
                    # but the point have not been processed yet.
                    progress_percentage = (current_log - 1.0 + (current_point - 1.0) / total_points) * 100.0
                    progress_percentage /= total_logs

                    self._manager.websocket.send(progress_message, 'ws_init', progress_percentage)

                    csv_data += "\n" + self._manager.system_settings.local_time(point['time'])
                    for header in display_headers:
                        for log_unit in header.table_units(self._cookie, 'log').values():
                            value = log_unit.get_string(self._node, point)
                            csv_data += "," + str(value)
                else:
                    csv_data = None
                    break

        return csv_data
