"""
Sleepy Mesh Scheduler Portion
"""

### INCLUDES ###
import logging

from gate.strings import AWAKE, SLEEP

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
    True: LOG_DUMP,
    False: LOG_DUMP_FAIL
}

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def _check_battery(node):
    """ Check battery voltage of a node, reset statistics if we get new battery """
    battery_voltage = None

    # Fetch battery value
    all_headers = node.read_headers('all')
    for header_name, header in all_headers.items():
        # FIXME: Probably not the best way to determine battery header
        if header_name == 'battery':
            battery_voltage = header.units('voltage').get_float(node)
            break

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
                # Check Platform #
                input_platform = self.platforms.platform_match(node, 'hw_type')

                if node['platform'] != input_platform:
                    LOGGER.warning("Platform of a node '" + str(node['net_addr']) + "' has been changed!")
                    LOGGER.warning("From '" + str(node['platform']) + "' to '" + str(input_platform) + "'!")

                    # Delete node that had its platform changed
                    self.platforms.delete_node(node)
                    node.delete()

                    continue

                # Parse Node Data #
                node.parse_data()

                if node['new_data']:
                    # Apply formulas to all headers of this node
                    all_headers = node.read_headers('all').values()
                    for header in all_headers:
                        header.apply_formulas(node)

                    # LOGGER.debug("Node: " + node['net_addr'])
                    # LOGGER.debug("Enables: " + str(node['live_enable']))
                    # LOGGER.debug("Raw Data: " + str(node['data_in']))
                    # LOGGER.debug("Processed Data: " + str(node['data_out']))

                if not node['presence']:
                    # Apply formulas to diagnostic headers (+ lq) of this node
                    all_headers = node.read_headers('all').values()
                    for header in all_headers:
                        if header['data_field'] in DIAGNOSTIC_FIELDS + ('lq', ):
                            header.apply_formulas(node)

                if node['presence']:
                    _check_battery(node)

            self.__validate_node_enables(node)

            # Dump Logs (if needed) #
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
        if not self.update_in_progress():
            if node.headers is not None:
                if node['presence'] and not node['inactive'] and node['type'] == 'node':
                    # Update headers (if needed)
                    header_enable = 0
                    for enable_type in ('live_enable', 'diagnostics'):
                        header_enable |= node.generate_enables(enable_type)

                    if node['raw_enables'] != header_enable:
                        LOGGER.warning('Node and header enables do not match!')
                        LOGGER.debug('Node Enable: {}'.format(node['raw_enables']))
                        LOGGER.debug('Header Enable: {}'.format(header_enable))

                        # Overwrite header values #
                        node['diagnostics'] &= node['raw_enables']
                        node['live_enable'] = node['raw_enables'] ^ node['diagnostics']

                        for enable_type in ('live_enable', 'diagnostics'):
                            node.generate_enables(enable_type, overwrite_headers=True)

                        # # Request node enables update #
                        # update_dict = {'raw_enables': header_enable}
                        # self.networks[0].request_update(update_dict, [node])

    def __complete_callback(self):
        """ Executes save complete callback (if needed) """
        if self.__save_complete_callback is not None:
            self.__save_complete_callback()
            self.__save_complete_callback = None
