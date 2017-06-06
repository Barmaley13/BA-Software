"""
Sleepy Mesh Scheduler Portion
"""

### INCLUDES ###
import logging

from gate.strings import AWAKE, SLEEP

from bridge import SNAP_POLL_DEVIATION
from network import SleepyMeshNetwork
from base import SleepyMeshBase
from node import DIAGNOSTIC_FIELDS


### CONSTANTS ###
## Strings ##
LOG_DUMP = "Automatic Log Dump was executed!"
LOG_DUMP_FAIL = "Automatic Log Dump failed!"

REBOOT_REQUEST = "Sending reboot request to base node!"

## Message Maps ##
LOG_DUMP_MESSAGE_MAP = {
    False: LOG_DUMP_FAIL,
    True: LOG_DUMP
}

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def _check_battery(node):
    """ Check battery voltage of a node, reset statistics if we get new battery """
    if node['presence']:
        # Fetch battery value
        all_headers = node.headers.read('all').values()
        for header in all_headers:
            # FIXME: Probably not the best way to determine battery header
            if header['internal_name'] == 'battery':
                battery_voltage = header.units('voltage').get_float(node)
                break
        else:
            battery_voltage = None

        # LOGGER.debug("Node '" + str(node['name']) + "' battery_voltage: " + str(battery_voltage))

        node.check_battery(battery_voltage)


### CLASSES ###
class SleepyMeshScheduler(SleepyMeshNetwork):
    def __init__(self, **kwargs):
        super(SleepyMeshScheduler, self).__init__(**kwargs)

        # Internal Members #
        self.__save_complete_callback = None

    ## Public Methods ##
    def init_scheduler(self):
        """ Starts scheduler, triggered by init procedure """
        self.__reset_flags()

        # Initialize values
        SleepyMeshBase._update_last_sync(self)

        # Calculate current draw while E10 was off (if possible)
        offline_time = self._current_period()
        if offline_time is not None:
            sleep_period = self.sleep_period()
            wake_period = self._wake_period()

            offline_period = sleep_period + wake_period

            period_number = int(offline_time / offline_period)
            period_remainder = offline_time % offline_period

            offline_awake_time = period_number * wake_period
            if period_remainder > 0:
                if (period_remainder / sleep_period) > 1:
                    offline_awake_time += period_remainder % sleep_period

            # LOGGER.debug('Offline Time: ' + str(offline_time))
            # LOGGER.debug('Offline Awake Time: ' + str(offline_awake_time))
            # LOGGER.debug('Period Number: ' + str(period_number))
            # LOGGER.debug('Period Remainder: ' + str(period_remainder))

            self._calculate_current_draw(offline_awake_time)

        # Start Scheduler
        self.resume_scheduler()

    def resume_scheduler(self, complete_callback=None):
        """ Resume scheduler either after stopping (or silencing) """
        LOGGER.debug('Resuming Scheduler!')

        self.__save_complete_callback = complete_callback
        self.bridge.base_node_ucast('smn__autopilot', True)
        self.bridge.base_node_ucast('smn__autopilot_notify', True)
        self.bridge.set_polling_mode('sleep')

        if not self._save_in_progress:
            self.__complete_callback()

    def silence_scheduler(self, complete_callback=None):
        """ Silences base scheduler """
        LOGGER.debug('Silencing Scheduler!')

        self.__save_complete_callback = complete_callback
        self.bridge.base_node_ucast('smn__autopilot_notify', False)
        self.bridge.set_polling_mode('sleep')

        if not self._save_in_progress:
            self.__complete_callback()

    def stop_scheduler(self, complete_callback=None):
        """ Stops Scheduler completely """
        LOGGER.debug('Stopping Scheduler!')

        self.__save_complete_callback = complete_callback
        self.bridge.base_node_ucast('smn__autopilot', False)
        self.bridge.base_node_ucast('smn__autopilot_notify', False)
        self.bridge.set_polling_mode('sleep')

        if not self._save_in_progress:
            self.__complete_callback()

    ## Private Methods ##
    # Sleepy Mesh Network States #
    def _awake(self):
        """
        Periodic Awake function
        Triggered by scheduler, scheduler set by _sleep function
        """
        self._mesh_awake = True

        self.__reset_flags()
        self.websocket.send(AWAKE, 'ws_awake')

        self.bridge.set_polling_mode('awake')

    # Sync Related Methods #
    def _sync(self, callback_type=None):
        """ Called either by successful sync or on timeout condition """
        if callback_type is None:
            callback_type = 'timeout'

        self._mesh_awake = False
        self._sync_type = callback_type
        SleepyMeshBase._update_last_sync(self)

        # Verify update (if update is in progress)
        self.networks[0].verify_update()

    def _sync_complete(self):
        """ Callback for sync complete """
        # Put bridge polling to sleep state
        self.bridge.set_polling_mode('sleep')

        self._update_statistics_data()
        self.__update_nodes_data()
        self.__update_system_data()

        self.save()
        self.__complete_callback()

        # Do not refresh current web page if update is in progress
        if self.update_in_progress():
            if self.update_in_progress('virgin'):
                self.uploader.check_upload('virgin')

            elif self.update_in_progress('base', 'node', 'gate'):
                if self.update_in_progress('base', 'gate'):
                    self.networks[0].execute_software_update(self.bridge.base)
                    self.bridge.check_base_node_reboot()

                if self.update_in_progress():
                    self.uploader.check_upload('_node')

            print(SLEEP)

        if not self.update_in_progress():
            if self.system_settings.virgins_enable:
                # Else search for virgins and current refresh web page
                self.networks[0].virgins.search(self._refresh_current_web_page)

            else:
                # Refresh Web Interface with new data
                self._refresh_current_web_page()

    def _refresh_current_web_page(self):
        """ Trigger web server to update all the information right after sync """
        self.websocket.send(SLEEP, 'ws_sleep')

    ## Class-Private Methods ##
    def __reset_flags(self):
        """ Resets flags across other instances """
        self.nodes.reset_flags()

        # Delete inactive nodes that have not been active on the network
        for net_addr, node in self.nodes.items():
            if node['inactive'] and not node['mcast_presence']:
                self.platforms.delete_node(node)

    def __update_nodes_data(self):
        """ Perform finalize sync procedures """
        log_dump_status = None
        last_sync = self['last_syncs'][-1]

        # Go through node list
        nodes = self.platforms.select_nodes('all')
        for node in nodes.values():
            node.update_last_sync(last_sync)

            if not node['inactive']:
                node.parse_data()

                if node['new_data']:
                    # Apply formulas to all headers of this node
                    all_headers = node.headers.read('all').values()
                    for header in all_headers:
                        header.apply_formulas(node)

                    # LOGGER.debug("Node: " + node['net_addr'])
                    # LOGGER.debug("Enables: " + str(node['live_enable']))
                    # LOGGER.debug("Raw Data: " + str(node['data_in']))
                    # LOGGER.debug("Processed Data: " + str(node['data_out']))

                elif not node['presence']:
                    # Apply formulas to diagnostic headers (+ lq) of this node
                    diagnostics_headers = node.headers.read('diagnostics').values()
                    for header in diagnostics_headers:
                        if header['data_field'] in DIAGNOSTIC_FIELDS + ('lq', ):
                            header.apply_formulas(node)

                _check_battery(node)

            self.__validate_node_enables(node)

            if not node['inactive']:
                _log_dump_status = node.update_logs()

                if _log_dump_status is not None:
                    if log_dump_status is None:
                        log_dump_status = _log_dump_status
                    else:
                        log_dump_status |= _log_dump_status

        # Prompt user about log dump (if needed)
        if log_dump_status is not None:
            if log_dump_status in LOG_DUMP_MESSAGE_MAP:
                message = LOG_DUMP_MESSAGE_MAP[log_dump_status]
                self.websocket.send(message, 'ws_reload')

    def __update_system_data(self):
        """ Update Modbus and SNMP Data """
        if self.system_settings.modbus_enable or self.system_settings.snmp_enable:
            nodes = self.platforms.select_nodes('active')

            if self.system_settings.modbus_enable:
                self.modbus_server.extract_data(nodes, self.system_settings)

            if self.system_settings.snmp_enable:
                self.snmp_server.parse_traps(nodes)

    def __validate_node_enables(self, node):
        """ Check node enables against header enables. Fix any inconsistencies. """
        if node['presence'] and not self.update_in_progress():
            if node['inactive']:
                for enable_type in ('live', 'log'):
                    if node.headers is not None:
                        # Overwrite headers
                        node.headers.node_enables(enable_type, node, overwrite_headers=True)
            else:
                # Update headers (if needed)
                update_dict = dict()

                for enable_type in ('live', 'log'):
                    header_enable = node.headers.node_enables(enable_type, node)
                    if node[enable_type + '_enable'] != header_enable:
                        LOGGER.warning('Node and header ' + enable_type + '_enables do not match!')
                        LOGGER.debug('Node ' + enable_type + '_enable: ' + str(node[enable_type + '_enable']))
                        LOGGER.debug('Header ' + enable_type + '_enable: ' + str(header_enable))
                        update_dict[enable_type + '_enable'] = header_enable

                if len(update_dict):
                    # Request node enables update
                    self.networks[0].request_update(update_dict, [node])

    def __complete_callback(self):
        """ Executes save complete callback (if needed) """
        if self.__save_complete_callback is not None:
            self.__save_complete_callback()
            self.__save_complete_callback = None
