"""
WebNetwork Class,
Responsible for requesting updates
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import copy
import logging

from gate import strings, conversions
from gate.sleepy_mesh import common

from base import NETWORK_DEFAULTS, NETWORK_UPDATE_TYPES
from callbacks import NetworkCallbacks
from virgins import Virgins


### CONSTANTS ###
## Battery Life Thresholds ##
SHORT_THRESHOLD = 30.0
REDUCED_THRESHOLD = 60.0

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class WebNetwork(NetworkCallbacks):
    """ Network Class that stores network updates and facilitates any network updates """
    def __init__(self, manager):
        super(WebNetwork, self).__init__(manager)

        self.virgins = None
        if self._manager.system_settings.virgins_enable:
            self.virgins = Virgins(self._manager)

    ## Public Methods ##
    def reset_network(self, force_reset=False, complete_callback=None):
        """ Reset network to defaults """
        reset_needed = False
        network_defaults = copy.deepcopy(NETWORK_DEFAULTS)

        self._update_complete_callback = complete_callback

        if force_reset:
            reset_needed = True
        else:
            # AES Fields trigger reset
            for aes_field in common.AES_FIELDS:
                if network_defaults[aes_field] is not None:
                    if network_defaults[aes_field] != self[aes_field]:
                        reset_needed = True
                        break

            # Any field triggers reset
            # for network_field, network_value in network_defaults.items():
            #     if network_value is not None:
            #         if network_value != self[network_field]:
            #             reset_needed = True
            #             break

        if reset_needed:
            self.request_update(network_defaults, complete_callback=None)

        else:
            self._complete_callback()

        return reset_needed

    def request_update(self, update_dict=None, nodes=None, complete_callback=None):
        """
        Checks if network update is pending. Request such update if needed.
        Can be also performed on a single node, if such node is provided

        :return: NA
        """
        # FIXME: Complete callback needs to be pared with the request.
        # Otherwise, we will have a problem if we a requesting update with a callback while other update is in progress
        self._update_complete_callback = complete_callback

        if update_dict is not None:
            if nodes is None:
                self.update_dict.update(update_dict)

            else:
                for node in nodes:
                    # This is made to update node's 'log_enables'
                    if 'type' in node and node['type'] == 'node':
                        for update_key, update_value in update_dict.items():
                            if update_key not in update_dict.keys() and update_key in node.keys():
                                node[update_key] = update_value

                    node.update_dict.update(update_dict)

        self._request_update(nodes)

        if not self.update_in_progress():
            self._complete_callback()

    def request_cancel_update(self):
        """ Request Cancel current update """
        if self.update_in_progress():
            self._cancel_update = True

    def power_consumption_state(self):
        """ Returns current power consumption state depending on current sleep time """
        output = 0

        if self['sleep'] < SHORT_THRESHOLD:
            output = 2
        elif self['sleep'] < REDUCED_THRESHOLD:
            output = 1

        return output

    ## Private Methods ##
    def _print_progress(self, node=None, append_message=None):
        """ Displays appropriate progress message depending on upload type """
        if self.update_in_progress():
            nodes = self._update_nodes
            total_nodes = len(nodes)

            current_node = 0
            for _node in nodes.values():
                current_node += int(_node['net_verify'] != self._cancel_update)

            progress_message = strings.UPLOAD_PROGRESS
            if node is not None:
                progress_message = strings.UPLOAD_NODE1 + str(node['name']) + strings.UPLOAD_NODE2
                progress_message += str(current_node + int(node['net_verify'] == self._cancel_update))
                progress_message += strings.UPLOAD_NODE3 + str(total_nodes)
                progress_message += strings.UPLOAD_NODE4

            progress_percentage = None
            if not self._manager.update_in_progress('gate', 'database_import'):
                node_progress_total_percentage = 95.0

                progress_percentage = (float(current_node) / float(total_nodes)) * node_progress_total_percentage

            self._manager.websocket.send(progress_message, 'ws_init', progress_percentage)
            if append_message:
                self._manager.websocket.send(append_message, 'ws_append', progress_percentage)

        else:
            super(WebNetwork, self)._print_progress(node, append_message)

    def _request_update(self, nodes):
        """ Updates fields and performs particular network update (if needed) """
        if nodes is None:
            update_type = 'network_update'
            update_dict = self.update_dict.compare(self)
            update_message = strings.UPDATING_NETWORK + self['net_id']

            self.__request_update(update_type, update_dict, update_message, nodes)

            # Execute update
            self._execute_update()

        else:
            for node in nodes:
                update_message = strings.UPDATING_NODE + node['net_addr']

                for update_type in ('node_update', 'inactive_update'):
                    # Node Update
                    if update_type == 'node_update':
                        update_dict = node.update_dict.compare(node)

                    # Inactive Update
                    else:
                        update_dict = node.update_dict.compare(self)

                    self.__request_update(update_type, update_dict, update_message, nodes)

            if not self.update_in_progress():
                # Preset Update
                for node in nodes:
                    if common.network_preset_needed(node):
                        self._start_update('preset_update', nodes)
                        break

            # Execute update
            self._execute_update(nodes[0])

    ## Class-Private Methods ##
    def __request_update(self, update_type, update_dict, update_message, nodes):
        update_fields = common.NETWORK_UPDATE_FIELDS
        if update_type == 'node_update':
            update_fields = common.NODE_UPDATE_FIELDS

        for field in update_fields:
            if field in update_dict.keys():
                if update_dict[field] is not None:
                    _update_message = strings.UPDATING1 + field
                    _update_message += strings.UPDATING2 + str(update_dict[field])
                    _update_message += update_message + '!'

                    self._manager.websocket.send(_update_message, 'ws_init')

                    if not self.update_in_progress():
                        self._manager.websocket.send(strings.SYNC_WAITING, 'ws_init')
                        self._start_update(update_type, nodes)
