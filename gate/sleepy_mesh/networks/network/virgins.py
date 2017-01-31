"""
Virgins Network Class
"""

### INCLUDES ###
import copy
import logging

from py_knife.ordered_dict import OrderedDict

from gate.conversions import bin_to_hex, hex_to_bin

### CONSTANTS ###
VIRGINS_DELAY = 1.0  # sec

## Virgin Args ##
VIRGIN_CALLS = OrderedDict()
VIRGIN_CALLS['mac'] = (4, 2)
VIRGIN_CALLS['name'] = (5,)
VIRGIN_CALLS['software'] = (10,)
VIRGIN_CALLS['raw_platform'] = (4, 41)

## Portal Address ##
PORTAL_NET_ADDR = "000001"

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)


### CLASSES ###
class Virgins(object):
    """ Virgins Class, performs virgin node search """
    def __init__(self, manager):
        self._manager = manager

        self._targets = None
        self._request_types = None
        self._search_complete_callback = None

    ## Virgin Methods ##
    def search(self, search_complete_callback):
        """ Function that looks for Virgin Nodes out there """
        self._search_complete_callback = search_complete_callback

        self._targets = None
        self._request_types = None

        self._manager.bridge.set_vm_stat_callback(self._start_search)
        self._manager.bridge.mcast_rpc('vmStat', *VIRGIN_CALLS['mac'])
        self._manager.bridge.schedule(VIRGINS_DELAY, self._search_callback)

    ## Virgin Callbacks ##
    def _start_search(self, mac):
        """ Function that updates virgin list """
        # This will protect from performing search during software upload
        if self._manager.bridge.get_vm_stat_callback() is not None:
            virgin_found = False

            # Ignore if a response is a blank
            # print "mac: " + str(mac)
            # print "type(mac): " + str(type(mac))
            if mac is not None and type(mac) in (str, unicode):
                # Convert binary to hex str
                mac_str = bin_to_hex(mac)
                net_addr_str = str(mac_str[10:16])

                # Ignore if response is received from Base node or Portal
                if net_addr_str != self._manager.bridge.gate['net_addr'] \
                        and net_addr_str != self._manager.bridge.base['net_addr'] \
                        and net_addr_str != PORTAL_NET_ADDR:

                    # Go through existing Virgin values
                    virgins = self._manager.platforms.select_nodes('virgins')
                    # LOGGER.debug("Virgins Table = " + str(virgins.keys()))
                    for net_addr, virgin in virgins.items():
                        # Compare Network Addresses
                        if net_addr == net_addr_str:
                            virgin['presence'] = True
                            virgin['mcast_presence'] = True
                            virgin['mcast_timeout'] = 0
                            virgin_found = True

                    # New Virgin
                    if not virgin_found:
                        new_virgin = {
                            'type': 'virgin',
                            'platform': 'virgins',
                            'mac': mac_str,
                            'net_addr': net_addr_str,
                            'raw_net_addr': hex_to_bin(net_addr_str),
                            'presence': True
                        }
                        self._manager.platforms.create_node(new_virgin)

                        LOGGER.debug("Virgins Table = " + str(virgins.keys()))
                        LOGGER.debug("New Virgin: " + net_addr_str)
                    else:
                        LOGGER.debug("Old Virgin: " + net_addr_str)

    def _search_callback(self, return_value=None):
        """ Function that parses virgin callbacks """
        # Create list of targets (if needed)
        if self._targets is None:
            self._targets = list()
            virgins = self._manager.platforms.select_nodes('virgins')
            for virgin in virgins.values():
                if virgin['presence']:
                    self._targets.append(virgin)

        if len(self._targets):
            if self._request_types is None:
                # Init virgin info fishing process
                self._request_types = copy.deepcopy(VIRGIN_CALLS.keys()[1:])
                self.__request_info()

            else:
                # Store incoming value
                if len(self._request_types):
                    self.__store_info(return_value)
                    del self._request_types[0]

                if len(self._request_types):
                    # Request next value
                    self.__request_info()
                else:
                    # Next target
                    del self._targets[0]
                    if len(self._targets):
                        self._request_types = copy.deepcopy(VIRGIN_CALLS.keys()[1:])
                        self.__request_info()
                    else:
                        self.__search_complete()

        else:
            self.__search_complete()

        # Do not reschedule
        return False

    ## Some Internal Methods ##
    def __store_info(self, return_value):
        """ Stores info from particular virgin """
        if len(self._targets) and len(self._request_types):
            virgins = self._manager.platforms.select_nodes('virgins')

            net_addr = self._targets[0]['net_addr']
            virgins[net_addr][self._request_types[0]] = return_value
            # self._targets[0][self._request_types[0]] = val
            LOGGER.debug("Virgin[" + str(net_addr) + "] " + self._request_types[0] + " = " + str(return_value))

    def __request_info(self):
        """ Requests info from particular virgin """
        if len(self._targets) and len(self._request_types):
            virgin_call = VIRGIN_CALLS[self._request_types[0]]
            self._manager.bridge.set_vm_stat_callback(self._search_callback)
            self._manager.bridge.com.rpc(self._targets[0]['raw_net_addr'], 'vmStat', *virgin_call)

    def __search_complete(self):
        """ Complete virgin search """
        # Return to normal mode
        self._manager.bridge.set_vm_stat_callback(None)

        # Clean up virgin list if needed
        virgins = self._manager.platforms.select_nodes('virgins')
        nodes = self._manager.platforms.select_nodes('all')
        for net_addr, virgin in virgins.items():
            if not(virgin['software'] is None or len(virgin['software']) == 0):
                self._manager.platforms.delete_node(virgin)
            elif net_addr in nodes.keys():
                # This is not a typical node any more - delete from the list
                if virgin['software'] == '':
                    LOGGER.warning("Node '" + str(net_addr) + "' appears to be virgin node!")
                    self._manager.platforms.delete_node(nodes[net_addr])

        if self._search_complete_callback is not None:
            self._search_complete_callback()
            self._search_complete_callback = None
