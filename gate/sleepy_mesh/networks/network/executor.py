"""
NetworkExecutor Class,
Responsible for executing different updates
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import logging

from gate import strings, conversions
from gate.sleepy_mesh import common

from base import NetworkBase


### CONSTANTS ###
## Message Maps ##
NOT_VERIFIED_MESSAGE_MAP = {
    False: strings.VERIFY_WAITING,
    True: strings.CANCEL_WAITING
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class NetworkExecutor(NetworkBase):
    ## Public Methods ##
    def verify_update(self, network_ready):
        """ Checks if network update has been verified """
        update_type = self.update_in_progress()
        if update_type:
            if update_type in ('network_update', 'preset_update'):
                # Trigger base node update
                base_node = self._manager.bridge.base
                self.execute_update(base_node)

            # Check if we can finalize network updates #
            all_verified = True
            for node in self._update_nodes.values():
                LOGGER.debug("Node: " + node['net_addr'])
                LOGGER.debug("Net Verify: " + str(node['net_verify']))

                all_verified &= bool(node['net_verify'] != self._cancel_update)

                if not all_verified:
                    break

            LOGGER.debug("All Verified: " + str(all_verified))

            if not all_verified:
                if self._cancel_update in NOT_VERIFIED_MESSAGE_MAP:
                    not_verified_message = NOT_VERIFIED_MESSAGE_MAP[self._cancel_update]
                    self._manager.websocket.send(not_verified_message, 'ws_init')

            elif update_type == 'node_update' or network_ready or self._cancel_update:
                self._finalize_update()

    def execute_update(self, node):
        """ Checks if network update failed on particular node """
        mcast_sync = True

        update_type = self.update_in_progress()
        update_node = bool(node['net_verify'] == self._cancel_update)
        if update_node:
            update_node &= bool(node['net_addr'] in self._update_nodes.keys())

            if update_type == 'network_update':
                update_node &= not node['inactive'] or node['type'] == 'base'

            elif update_type == 'inactive_update':
                update_node &= node['inactive'] and node['type'] != 'base'

            elif update_type == 'preset_update':
                update_node &= common.network_preset_needed(node)

        if update_node:
            if update_type != 'node_update':
                mcast_sync &= False
                node['off_sync'] = True

            update_message = self._update_message(node)
            if update_message is not None:
                if not self._cancel_update:
                    update_message += strings.REQUEST_UPDATE
                else:
                    update_message += strings.REQUEST_CANCEL_UPDATE

                self._print_progress(node, update_message)

            self.__update_node(node)

        return mcast_sync

    ## Private Methods ##
    def execute_software_update(self, node):
        """ Execute software updates on a node """
        mcast_sync = True

        if node['software_update']:
            # Do not sync if software update in progress!
            software_upload_in_progress = self._manager.uploader.check_upload(node['type'])
            mcast_sync &= not software_upload_in_progress

        elif node['post_software_update']:
            # Perform post software update procedures
            update_args = [node['net_addr'], 'nv__post_software_update']
            self._manager.bridge.network_ucast(*update_args)

            if node['type'] == 'base':
                LOGGER.debug("Base Update Args: " + str(update_args))
            else:
                LOGGER.debug("Node Update Args: " + str(update_args))

            node['post_software_update'] = False

        return mcast_sync

    ## Class-Private Methods ##
    def __update_node(self, node):
        """ Function sends RPC to update particular node """
        update_args = ['smn__net_update']
        update_type = self.update_in_progress()

        # Patch for now
        if update_type != 'node_update':
            # Old functionality
            # if update_type == 'node_update':
            #     update_args = ['smn__node_update']

            update_args += self._update_args(node)

            if node['type'] == 'base':
                self._manager.bridge.base_node_ucast(*update_args)
                LOGGER.debug("Base Update Args: " + str(update_args))

            elif node['type'] == 'node':
                update_args = [node['net_addr']] + update_args
                self._manager.bridge.network_ucast(*update_args)
                LOGGER.debug("Node Update Args: " + str(update_args))

    def _update_args(self, node):
        """
        Creates network update arguments that are passed to rpc function and send to particular node/nodes

        :param node: Node, that we are working with
        :return: tuple with update arguments
        """
        output = list()

        update_dict = self._update_dict(node)
        # LOGGER.debug("Node Update Dict: " + str(update_dict))

        for field in update_dict.keys():
            arg = update_dict[field]
            if field in common.TIMEOUT_FIELDS:
                # get_int_rem returns tuple already
                output += list(conversions.get_int_rem(arg))

            elif field in common.CYCLE_FIELDS:
                output += list(conversions.get_base_int_rem(arg))

            else:
                output += [arg]

        return output
