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
from gate.sleepy_mesh.node import common
from gate.sleepy_mesh.node.headers import generate_sensor_types

from executor import NetworkExecutor


### CONSTANTS ###
## Callback Arguments ##
SHORT_LOG_FIELDS = ('raw_net_addr', 'raw_enables', 'raw_data', 'raw_lq', 'raw_error')
LONG_LOG_FIELDS = ('name', 'raw_mac', 'raw_platform', 'raw_enables', 'firmware', 'software', 'raw_error')
PRIMARY_NETWORK_LOG_FIELDS = ('raw_net_addr', ) + common.NETWORK_FIELDS
NETWORK_LOG_FIELDS = PRIMARY_NETWORK_LOG_FIELDS + common.RAW_TIMEOUT_FIELDS
BASE_LOG_FIELDS = PRIMARY_NETWORK_LOG_FIELDS + common.RAW_CYCLES_FIELDS

## Callback Fields Map ##
CALLBACK_FIELDS_MAP = {
    'long': LONG_LOG_FIELDS,
    'short': SHORT_LOG_FIELDS,
    'network': NETWORK_LOG_FIELDS,
    'base': BASE_LOG_FIELDS
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def __parse_callback_data(raw_dict):
    """ Convert raw mac or network address """
    # Generic Fields #
    if 'raw_mac' in raw_dict:
        # raw_net_addr = raw_mac[5:8]
        raw_dict['mac'] = conversions.bin_to_hex(raw_dict['raw_mac'])
        raw_dict['net_addr'] = raw_dict['mac'][10:16]
        del raw_dict['raw_mac']

    elif 'raw_net_addr' in raw_dict:
        raw_dict['net_addr'] = conversions.bin_to_hex(raw_dict['raw_net_addr'])
        del raw_dict['raw_net_addr']

    # Short/Long Log Fields #
    if 'name' in raw_dict:
        # Protect name from None value
        if raw_dict['name'] is None:
            raw_dict['name'] = ""

    if 'raw_platform' in raw_dict:
        raw_dict['raw_platform'] = raw_dict['raw_platform'].lower()
        raw_dict['sensor_type'] = generate_sensor_types(raw_dict['raw_platform'])

    for field in ('raw_enables', 'raw_lq', 'raw_error') + common.RAW_CYCLES_FIELDS + common.RAW_TIMEOUT_FIELDS:
        if field in raw_dict and type(raw_dict[field]) not in (int, long):
            # LOGGER.debug("Overwriting field: " + str(field))
            raw_dict[field] = conversions.bin_to_int(raw_dict[field])
            # LOGGER.debug('raw_dict[field]: ' + str(raw_dict[field]))

    # Network Log Fields #
    network_fields = common.CYCLE_FIELDS + common.TIMEOUT_FIELDS
    for field in network_fields:
        field_integer = field + '_integer'
        field_remainder = field + '_remainder'

        if field_integer in raw_dict and field_remainder in raw_dict:
            _get_float = conversions.get_float
            if field in common.CYCLE_FIELDS:
                _get_float = conversions.get_base_float

            raw_dict[field] = _get_float(raw_dict[field_integer], raw_dict[field_remainder])
            del raw_dict[field_integer]
            del raw_dict[field_remainder]

    return raw_dict


def get_input_dict(callback_type, *callback_args):
    """ Convert callback_args to dictionary format """
    output = None

    if callback_type in CALLBACK_FIELDS_MAP:
        fields = CALLBACK_FIELDS_MAP[callback_type]
        if len(fields) == len(callback_args):
            raw_dict = dict(zip(fields, callback_args))

            # LOGGER.debug('callback_type:' + str(callback_type))
            # LOGGER.debug('raw_dict:' + str(raw_dict))

            output = __parse_callback_data(raw_dict)

    return output


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

        input_dict = get_input_dict(callback_type, *args)
        if input_dict is not None:
            LOGGER.debug('callback_type: {}'.format(callback_type))
            LOGGER.debug('input_dict: {}'.format(input_dict))

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

        return node

    def _network_update_callback(self, callback_type, *args):
        """
        Base/Node Callback. Verifies that network update was successful
        If one of the node fails update this method will retry to update that particular node
        """
        input_dict = get_input_dict(callback_type, *args)

        if input_dict is not None:
            # Verify appropriate node
            net_addr = input_dict['net_addr']
            nodes = self._update_nodes
            if net_addr in nodes.keys():
                node = nodes[net_addr]

                if node['type'] == 'base':
                    input_dict = get_input_dict('base', *args)

                # LOGGER.debug("Network Log Dict: " + str(input_dict))

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
