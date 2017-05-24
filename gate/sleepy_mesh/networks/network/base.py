"""
Network Base Class
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import os
import copy
import logging

from py_knife.ordered_dict import OrderedDict

from gate import strings
from gate import conversions
from gate.database import DatabaseDict
from gate.sleepy_mesh import common


### CONSTANTS ###
## Network Defaults Constants ##
DEFAULT_WAKE_TIME = 2.0             # Overall Value, divide by 2 to get +/- value
DEFAULT_SLEEP_TIME = 5.0
DEFAULT_TIMEOUT_WAKE_TIME = DEFAULT_SLEEP_TIME
DEFAULT_TIMEOUT_SLEEP_TIME = DEFAULT_TIMEOUT_WAKE_TIME * (DEFAULT_SLEEP_TIME / DEFAULT_WAKE_TIME)

## Network Defaults Dictionary ##
NETWORK_DEFAULTS = {
    'net_id': '1C2C',
    'channel': 4,
    'data_rate': 0,
    'aes_key': '',
    'aes_enable': 0,
    'wake': DEFAULT_WAKE_TIME,
    'sleep': DEFAULT_SLEEP_TIME,
    'timeout_wake': DEFAULT_TIMEOUT_WAKE_TIME,
    'timeout_sleep': DEFAULT_TIMEOUT_SLEEP_TIME,
    'firmware': None,
    'software': None
}

## Network Update Types ##
NETWORK_UPDATE_TYPES = ('network_update', 'inactive_update', 'preset_update', 'node_update')

## Message Maps ##
UPDATE_COMPLETE_MESSAGE_MAP = {
    False: strings.UPDATE_COMPLETE,
    True: strings.UPDATE_CANCELLED
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class NetworkBase(DatabaseDict):
    """ Network Class that stores network updates and facilitates any network updates """
    def __init__(self, manager):
        self._manager = manager

        self.update_dict = common.UpdateDict(common.NETWORK_UPDATE_FIELDS)
        self._update_complete_callback = None

        # Create Defaults
        network_defaults = copy.deepcopy(NETWORK_DEFAULTS)

        # Initialize Database Entry
        super(NetworkBase, self).__init__(
            db_file=os.path.join('networks', network_defaults['net_id'] + '.db'),
            defaults=network_defaults
        )

        ## Internal Variables ##
        self._update_interface = self._manager.update_interfaces.create(NETWORK_UPDATE_TYPES)
        self.update_in_progress = self._update_interface.update_type

        self._bridge_reboot_required = False
        self._aes_update_required = False
        self._cancel_update = False

        self._update_nodes = self.__generate_update_nodes()

    ## Public Methods ##
    def _start_update(self, update_type, nodes=None):
        """ Starts network update """
        # Patch for now
        if update_type != 'node_update':
            self._manager.autopilot(False)

        self._update_interface.start_update(update_type)
        self._update_nodes = self.__generate_update_nodes(nodes)

    def _finish_update(self, finish_message=None):
        """ Finishes update """

        if self.update_in_progress():
            if not self._manager.update_in_progress('gate', 'database_import'):
                self._update_interface.finish_update(finish_message)

            else:
                self._update_interface.finish_update(None)
                self._print_progress(finish_message)

        self._cancel_update = False
        self._update_nodes = self.__generate_update_nodes()

        self._manager.autopilot(True)

    ## Private Methods ##
    def _update_dict(self, node):
        """
        Provides update dictionary depending on the current state of the network

        :param node: Provide node
        :return: Network update dictionary
        """
        output = OrderedDict()

        # Select dictionary
        _update_dict = self
        _current_dict = self

        update_type = self.update_in_progress()
        # Format dictionary
        update_fields = common.NODE_NETWORK_FIELDS
        if node['type'] == 'base':
            update_fields = common.BASE_NETWORK_FIELDS

        if update_type == 'node_update':
            _update_dict = node.update_dict
            _current_dict = node
            update_fields = common.NODE_UPDATE_FIELDS

        elif update_type in ('network_update', 'inactive_update') and not self._cancel_update:
            if update_type == 'network_update':
                _update_dict = self.update_dict

            elif update_type == 'inactive_update':
                _update_dict = node.update_dict

        for field in update_fields:
            if field in _update_dict.keys():
                if _update_dict[field] is None:
                    output[field] = _current_dict[field]
                else:
                    output[field] = _update_dict[field]

                    if update_type == 'network_update' and field in common.NETWORK_FIELDS:
                        self._bridge_reboot_required = True
                        if field == 'aes_enable':
                            self._aes_update_required = True
            else:
                output[field] = _current_dict[field]

        return output

    def _update_message(self, node=None):
        """ Generates update message for particular node """
        update_message = None

        update_type = self.update_in_progress()
        if update_type in ('network_update', 'inactive_update'):
            update_message = strings.NETWORK_UPDATE

        elif update_type == 'preset_update':
            update_message = strings.PRESET_UPDATE

        elif update_type == 'node_update':
            update_message = strings.NODE_UPDATE

        if update_message is not None and node is not None:
            # Check if its a base node or not
            if update_type == 'inactive_update':
                update_message += strings.INACTIVE_NODE_UPDATE

            else:
                if node['type'] == 'base':
                    update_message += strings.BASE_NODE_UPDATE
                else:
                    update_message += strings.NODE_NODE_UPDATE

            update_message += node['net_addr']

        return update_message

    def _node_verify(self, node, input_dict):
        """ Performs node verify procedure """
        if node['net_addr'] in self._update_nodes.keys():
            # Execute verify routine
            verified = self.__compare_dicts(node, input_dict)
            node['net_verify'] = bool(verified != self._cancel_update)
            # LOGGER.debug('Node net_verify:' + str(node['net_verify']))

            if verified:
                update_message = self._update_message(node)
                if not self._cancel_update:
                    update_message += strings.SUCCESS_UPDATE
                else:
                    update_message += strings.SUCCESS_CANCEL_UPDATE

                self._print_progress(node, update_message)

    def _print_progress(self, node=None, append_message=None):
        """ Displays appropriate progress message depending on upload type """
        self._manager.websocket.send(append_message)

    def _finalize_update(self):
        """ Very last step of the network update procedure """
        update_type = self.update_in_progress()
        if update_type != 'node_update' and not self._cancel_update:
            # Finalize network update
            for node in self._update_nodes.values():
                if node['net_verify']:
                    update_args = [node['net_addr'], 'smn__net_reboot']
                    self._manager.bridge.network_ucast(*update_args)

                    if node['type'] == 'base':
                        LOGGER.debug("Base Update Args: " + str(update_args))
                    else:
                        LOGGER.debug("Node Update Args: " + str(update_args))

            # bridge_reboot_required Set?
            # LOGGER.debug("Bridge Reboot Required = " + str(self._bridge_reboot_required))
            if self._bridge_reboot_required:
                # Yes => Reboot bridge node
                self._manager.bridge.request_base_node_reboot()

            else:
                self._update_completed()

        else:
            self._update_completed()

    def _update_completed(self):
        """ Perform update complete procedures """
        # Perform specific network procedures
        update_type = self.update_in_progress()
        if update_type in ('network_update', 'inactive_update') and self._cancel_update:
            # Reset values in update_dict
            self.update_dict.reset()

        elif update_type == 'network_update':
            # Move values to main dict
            for field in common.NETWORK_UPDATE_FIELDS:
                if field in self.update_dict.keys():
                    if self.update_dict[field] is not None:
                        self[field] = self.update_dict[field]

        # Delete inactive nodes after performing network update or inactive update
        if update_type in ('network_update', 'inactive_update'):
            inactive_nodes = self._manager.platforms.select_nodes('inactive')
            for node in inactive_nodes.values():
                self._manager.platforms.delete_node(node)

        # Reset net_verify flags
        for node in self._update_nodes.values():
            if node['net_verify']:
                node['net_verify'] = False

                if update_type == 'preset_update':
                    node['off_sync'] = False
                    node['network_preset'] = True

                # Finalise network preset
                if update_type in ('network_update', 'preset_update'):
                    if node['type'] == 'node':
                        self._manager.bridge.network_ucast(node['net_addr'], 'smn__short_ack')

        # Prompt about our success or failure
        update_complete_message = None
        if self._cancel_update in UPDATE_COMPLETE_MESSAGE_MAP:
            update_complete_message = self._update_message()
            update_complete_message += UPDATE_COMPLETE_MESSAGE_MAP[self._cancel_update]

        self._finish_update(update_complete_message)

        self._manager.platforms.save()
        if update_type != 'node_update':
            self.save()

        self._complete_callback()

    def _complete_callback(self):
        """ Executes update complete callback (if needed) """
        if self._update_complete_callback is not None:
            self._update_complete_callback()
            self._update_complete_callback = None

    ## Class-Private Methods ##
    def __generate_update_nodes(self, nodes=None):
        """ Locate appropriate nodes """
        _nodes = self._manager.platforms.select_nodes('active')
        _nodes[self._manager.bridge.base['net_addr']] = self._manager.bridge.base

        update_type = self.update_in_progress()
        if update_type in ('node_update', 'inactive_update', 'preset_update'):
            if update_type == 'node_update':
                _nodes = self._manager.platforms.select_nodes('all')
            elif update_type == 'inactive_update':
                _nodes = self._manager.platforms.select_nodes('inactive')
            elif update_type == 'preset_update':
                _preset_nodes = OrderedDict()
                for net_addr, node in _nodes.items():
                    if common.network_preset_needed(node):
                        _preset_nodes[net_addr] = node

                _nodes = _preset_nodes

            if nodes is not None:
                output = OrderedDict()
                for node in nodes:
                    net_addr = node['net_addr']
                    if net_addr in _nodes.keys():
                        output[net_addr] = node

            else:
                output = _nodes

        else:
            output = _nodes

        # LOGGER.debug("Update Nodes: " + str(output.keys()))

        return output

    def __compare_dicts(self, node, input_dict):
        """
        Compares values of incoming dictionary to update dictionary

        :param node: Node we are working with
        :param input_dict: Input dictionary fetched from callback
        :return: Boolean indicating if those network update values are identical
        """
        update_dict = self._update_dict(node)
        # LOGGER.debug('input_dict: ' + str(input_dict))
        # LOGGER.debug('update_dict: ' + str(update_dict))

        identical = True
        for field in update_dict.keys():
            if field in input_dict.keys():
                update_value = update_dict[field]
                if field in common.TIMEOUT_FIELDS:
                    update_value = conversions.round_float(update_value)
                elif field in common.CYCLE_FIELDS:
                    update_value = conversions.round_base_float(update_value)

                identical &= bool(input_dict[field] == update_value)
                if not identical:
                    break

        # LOGGER.debug('verified: ' + str(identical))

        return identical
