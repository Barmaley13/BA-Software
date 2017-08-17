"""
Network Callbacks Class,
Collection of class callback methods executed during normal network operation and/or network update
Responsible for updating either whole network or a particular nodes with new network parameters
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import logging

from gate import strings
from gate import conversions
from gate.sleepy_mesh import common

from executor import NetworkExecutor


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class NetworkCallbacks(NetworkExecutor):
    ## Public Methods ##
    def callback(self, callback_type, *args):
        """ Main network callback method """
        output = None

        callback_map = {
            'long': self._node_callback,
            'short': self._node_callback,
            'network': self._network_update_callback,
            'base_reboot': self._base_reboot_callback
        }
        if callback_type in callback_map:
            callback = callback_map[callback_type]
            output = callback(callback_type, *args)

        else:
            LOGGER.error("Callback type '" + str(callback_type) + "' does not exists!")

        return output

    def _node_callback(self, callback_type, *args):
        """ Called by nodes """
        node = None

        input_dict = common.get_input_dict(callback_type, *args)
        if input_dict is not None:
            # LOGGER.debug(callback_type.title() + " Log Dict: " + str(input_dict))

            # Find Node #
            nodes = self._manager.platforms.select_nodes('all')
            for _node in nodes.values():
                node_found = bool(_node['net_addr'] == input_dict['net_addr'])

                if node_found:
                    node = _node
                    # LOGGER.debug('Node: ' + str(node['net_addr']))

                    # Update node with incoming data
                    node.update(input_dict)

                    # Perform updates (if needed)
                    if not self.update_in_progress():
                        self.execute_software_update(node)

                    if not self.update_in_progress():
                        self._request_update([node])

                    update_type = self.update_in_progress()
                    if update_type:
                        if update_type == 'node_update':
                            # LOGGER.debug('Verifying node_update')
                            self._node_verify(node, input_dict)

                        # Execute update if initial attempt failed
                        self.execute_update(node)

            # Create if not found #
            if node is None:
                if callback_type == 'long':
                    node = self._manager.platforms.create_node(input_dict)
                    node['off_sync'] = False

                else:
                    self._request_long_ack(input_dict['net_addr'])

            else:
                if callback_type == 'long':
                    # Check if platform changed
                    input_platform = self._manager.platforms.platform_match(input_dict, 'hw_type')

                    if node['platform'] != input_platform:
                        LOGGER.warning("Platform of a node '" + str(node['net_addr']) + "' has been changed!")
                        LOGGER.warning("From '" + str(node['platform']) + "' to '" + str(input_platform) + "'!")

                        # Delete node that had its platform changed
                        self._manager.platforms.delete_node(node)
                        node.delete()

                        node = self._manager.platforms.create_node(input_dict)

        return node

    def _network_update_callback(self, callback_type, *args):
        """
        Base/Node Callback. Verifies that network update was successful
        If one of the node fails update this method will retry to update that particular node
        """
        input_dict = common.get_input_dict(callback_type, *args)

        if input_dict is not None:
            # Verify appropriate node
            net_addr = input_dict['net_addr']
            nodes = self._update_nodes
            if net_addr in nodes.keys():
                node = nodes[net_addr]

                if node['type'] == 'base':
                    input_dict = common.get_input_dict('base', *args)

                LOGGER.debug("Network Log Dict: " + str(input_dict))

                ## Network update verify ##
                update_type = self.update_in_progress()
                if update_type in ('network_update', 'inactive_update', 'preset_update'):
                    # Verify that updates were properly executed
                    self._node_verify(node, input_dict)

            else:
                # This node will be ignored during network update
                nodes = self._manager.platforms.select_nodes('all')
                if net_addr in nodes:
                    node = nodes[net_addr]
                    update_message = self._update_message(node)
                    if update_message is not None:
                        update_message += strings.IGNORED_UPDATE
                        self._manager.websocket.send(update_message, 'ws_init')

    def _base_reboot_callback(self, callback_type, *args):
        """ Reboot confirmation triggered by Base node """
        self._manager.websocket.send(strings.BASE_REBOOT_COMPLETED, 'ws_init')

        if self._aes_update_required:
            self._aes_update_required = False
            self._manager.bridge.set_aes_nv_parameters(self.update_dict)

    ## Overwrite Methods ##
    def _request_update(self, nodes):
        """ Blank method should be overwritten by a parent class """
        LOGGER.error("Method _request_update is not implemented!")
        raise NotImplementedError
