"""
Sleepy Mesh Package includes number of modules supporting Sleepy Mesh Network Implementation
This __init__ module contains SleepyMeshManager class, which is responsible for::

    * Contains all the sleepy mesh subclasses
    * Sleep Awake Cycles Scheduling
    * Pause/Resume Scheduler
    * Syncing Functionality

Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import os
import sys
# import time
import logging

from py_knife import platforms
from py_knife.ordered_dict import OrderedDict

# from gate.common import AUTO_FILE
from gate.strings import REBOOT, RESTART_REQUIRED
from gate.conversions import bin_to_hex, get_base_float

from error import OLD_SOFTWARE_DETECTED
from common import network_preset_needed, parse_raw_data, CALLBACK_FIELDS_MAP
from base import SYNC_TYPES
from networks import NETWORK_UPDATE_TYPES
from scheduler import SleepyMeshScheduler
from statistics import SYSTEM_STATISTICS_FILE


### CONSTANTS ###
# Automatic Refresh Info after bridge reboot
BRIDGE_REFRESH_INFO_DELAY = 1.5     # seconds

## Strings ##
GATE_ADDR = "Gate Network Address: "
BASE_ADDR = "Base Network Address: "
BASE_FIRMWARE = "Base Firmware: "
BASE_SOFTWARE = "Base Software: "
BASE_CHANNEL = "Base Channel: "
BASE_DATA_RATE = "Data Rate: "

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class SleepyMeshManager(SleepyMeshScheduler):
    """ Class managing sleepy mesh network (Sleep/Wake cycles) """
    def __init__(self, **kwargs):
        super(SleepyMeshManager, self).__init__(**kwargs)

        # External Members #
        self.reboot_flag = False

        self._read_statistics = False

    ## Public Methods ##
    def start(self):
        """ Procedure that starts Manager and the whole Sleepy Mesh Network """
        bridge_init_info = {
            ## Callbacks added prior to bridge initialization ##
            'pre_init_callbacks': {
                # Snap Connect Callbacks #
                'brg__request': self.bridge.base_node_request_callback
            },
            ## Callbacks added after bridge initialization ##
            'post_init_callbacks': {
                # Bridge Callbacks
                'tellVmStat': self.bridge.tell_vm_stat,
                'su_recvd_reboot': self.bridge.su_recvd_reboot,

                # Networks Callbacks
                'brg__reboot': self._base_reboot_callback,
                'smn__net_log': self._network_update_callback,

                # Platforms/Nodes Callbacks
                'smn__long_log': self._long_callback,
                'smn__short_log': self._short_callback,

                'brg__notify': self._bridge_notify,
                'brg__data': self._bridge_data,
                'brg__statistics': self._bridge_statistics
            },
            # Handlers #
            'init_complete_handler': self._bridge_init_complete,
            'sync_complete_handler': self._sync_complete_handler,
            # Initial NV Parameters #
            'init_nv_param': {
                'aes_key': self.networks[0]['aes_key'],
                'aes_enable': self.networks[0]['aes_enable']
            },
            'requests': [
                {
                    'request': 'rpcSourceAddr',
                    'reference': self.bridge.gate,
                    'reference_key': 'net_addr',
                    'description': GATE_ADDR,
                    'post_processing': bin_to_hex
                },
                {
                    'request': 'localAddr',
                    'reference': self.bridge.base,
                    'reference_key': 'net_addr',
                    'description': BASE_ADDR,
                    'post_processing': bin_to_hex
                },
                {
                    'request': 'getChannel',
                    'reference': self.networks[0],
                    'reference_key': 'channel',
                    'description': BASE_CHANNEL
                },
                {
                    'request': 'nv__get_data_rate',
                    'reference': self.networks[0],
                    'reference_key': 'data_rate',
                    'description': BASE_DATA_RATE
                },
                {
                    'request': 'nv__get_firmware',
                    'reference': (self.networks[0], self.bridge.base),
                    'reference_key': 'firmware',
                    'description': BASE_FIRMWARE
                },
                {
                    'request': 'nv__get_software',
                    'reference': (self.networks[0], self.bridge.base),
                    'reference_key': 'software',
                    'description': BASE_SOFTWARE
                }
            ]
        }

        self.bridge.init(bridge_init_info)

    def update_timing(self, time_diff):
        """ Updates last sync timing and node creation time stamps and log timing """
        # Update Last Sync
        for last_sync in self['last_syncs']:
            last_sync += time_diff

        for node in self.platforms.select_nodes('active').values():
            node.update_timing(time_diff)

    def refresh_bridge_info(self):
        """ Request to refresh bridge info """
        self.bridge.schedule(BRIDGE_REFRESH_INFO_DELAY, self.bridge.refresh_info)

    # TODO: Change reboot to GATE instance reload?
    def reboot(self):
        """ Reboot the system """
        if self.reboot_flag:
            self.websocket.send(REBOOT)

            if platforms.PLATFORM in platforms.EMBEDDED_PLATFORMS:
                os.system('reboot')

                # if os.path.isfile(AUTO_FILE):
                #     os.system(AUTO_FILE + ' restart')
                # else:
                #     os.system('reboot')

            # FIXME: Restart the script, not reboot!!??
            else:
                sys.exit(RESTART_REQUIRED)

    def reload_databases(self):
        """ Reload Databases """
        databases = [
            self.system_settings,
            self.snmp_server.queue,
            self.snmp_server.agents,
            self.snmp_server.commands,
            self.snmp_server.traps,
            self.modbus_server,
            self.snmp_server,
            self.nodes,
            self.platforms,
            self.networks,
            self
        ]

        # Note: statistics (AKA self) is not included

        for database in databases:
            database.load()

    # Misc Buffer Methods #
    def reset_network(self, *args, **kwargs):
        """ Reset network to defaults """
        return self.networks[0].reset_network(*args, **kwargs)

    def request_update(self, *args, **kwargs):
        self.networks[0].request_update(*args, **kwargs)

    ## Private Methods ##
    def _bridge_init_complete(self):
        """ Perform various procedures before starting scheduler """
        # Overwrite Base Wake and Sleep values
        base_node = self.bridge.base
        if network_preset_needed(base_node):
            self.networks[0].request_update(nodes=[base_node])
            self.networks[0].execute_update(base_node)

        else:
            self.init_scheduler()

    def _bridge_notify(self, bridge_state, bridge_message):
        """ Notify gate when one of the bridge states have changed """
        if bridge_state in ('sleep', 'off_sync'):
            self._read_statistics = bool(bridge_state == 'sleep')
            self.bridge.base_node_ucast('smn__get_node_data')

        elif bridge_state == 'awake':
            self._awake()

        elif bridge_state == 'sync':
            callback_type = None
            for _callback_type in SYNC_TYPES.keys():
                if _callback_type in bridge_message:
                    callback_type = _callback_type

            self._sync(callback_type)

        if bridge_state in ('sync', 'off_sync'):
            self.websocket.send(bridge_message)

    def _bridge_data(self, raw_data, last_packet):
        """ Bridge returning data to the gate """
        if raw_data is not None and len(raw_data):
            while len(raw_data):
                raw_packet, raw_data = parse_raw_data(raw_data)

                if raw_packet is None:
                    break

                else:
                    raw_node_args = list()
                    while len(raw_packet):
                        raw_node_arg, raw_packet = parse_raw_data(raw_packet)
                        raw_node_args.append(raw_node_arg)

                        if raw_node_arg is None:
                            break

                    if len(raw_node_args):
                        callback_type = raw_node_args[0]
                        del raw_node_args[0]

                        # LOGGER.debug("callback_type: " + str(callback_type))
                        # LOGGER.debug("raw_node_args length: " + str(len(raw_node_args)))

                        self.networks[0].callback(callback_type, *raw_node_args)

        if self._read_statistics and last_packet:
            self.bridge.base_node_ucast('smn__get_statistics')

    def _bridge_statistics(self, sync_current, delay_current):
        """ Bridge returning statistics data """
        statistics_map = OrderedDict()
        statistics_map['sync_current'] = sync_current
        statistics_map['delay_current'] = delay_current

        for statistics_key, statistics_value in statistics_map.items():
            if statistics_value is not None:
                statistics_value = get_base_float(statistics_value, 0)
            self['data_in'][statistics_key] = statistics_value

        self._sync_complete_handler(self._mcast_sync_id)

    # Various Callbacks #
    def _base_reboot_callback(self, *args):
        """ Modified base reboot callback """
        # Don't really need to pass *args but we do so for compatibility
        if self.update_in_progress('gate') and self.update_in_progress('network_update'):
            self.networks[0].callback('base_reboot', *args)
            self.uploader.base_reboot_callback(*args)

        elif self.networks[0].update_in_progress():
            self.networks[0].callback('base_reboot', *args)

        elif self.update_in_progress('base', 'gate'):
            self.uploader.base_reboot_callback(*args)

        self.refresh_bridge_info()

    def _network_update_callback(self, *args):
        """ Called by nodes after network update call as a confirmation """
        self.networks[0].callback('network', *args)

        if network_preset_needed(self.bridge.base):
            self.networks[0].verify_update(True)
            self.init_scheduler()

    def _long_callback(self, *args):
        """
        Called by nodes on init, reboot or update
        Function check if node has been discovered already
        Appends list if node is new
        Updates node's entry with new variables if found
        """
        self._callback('long', *args)

    def _short_callback(self, *args):
        """
        Called by nodes on each wake up
        Files network address and optionally ADC values
        """
        self._callback('short', *args)
