"""
Sleepy Mesh Scheduler Portion
"""

### INCLUDES ###
import logging

from distutils.version import StrictVersion

from gate.strings import AWAKE, SLEEP
from gate.conversions import find_version

from bridge import SNAP_POLL_DEVIATION
from network import SleepyMeshNetwork
from base import SleepyMeshBase
from node import DIAGNOSTIC_FIELDS


### CONSTANTS ###
AUTOPILOT_BASE_VERSION = 'BASE_1.27'

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
        self._pause = True

        self._autopilot_present = False

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

        # Determine auto pilot presence
        base_software = self.bridge.base['software']
        current_base_version = StrictVersion(find_version(base_software))
        autopilot_base_version = StrictVersion(find_version(AUTOPILOT_BASE_VERSION))
        self._autopilot_present = bool(current_base_version >= autopilot_base_version)

        # Start Scheduler
        autopilot_state = not self.networks[0].update_in_progress()
        self.resume_scheduler(autopilot_state)

    def autopilot(self, autopilot_state=None):
        """
        Turn "autopilot" mode on base node on/off.
        Mode where base node is responsible for generating sleepy mesh cycles
        """
        if self._autopilot_present:
            if autopilot_state is not None:
                self._autopilot_state = autopilot_state

                LOGGER.debug('Autopilot: ' + str(autopilot_state))
                if autopilot_state:
                    self._pause_scheduler()

                    self.bridge.base_node_ucast('smn__autopilot', autopilot_state)
                    self.bridge.base_node_ucast('smn__autopilot_notify', autopilot_state)

                else:
                    self.bridge.base_node_ucast('smn__autopilot', autopilot_state)
                    # self.bridge.base_node_ucast(
                    #     'callback', 'brg__stop_scheduler', 'smn__autopilot_notify', autopilot_state)

                    self.bridge.base_node_ucast('smn__autopilot_notify', autopilot_state)
                    self._resume_scheduler()

                    self._complete_callback()

        return self._autopilot_state

    def resume_scheduler(self, autopilot_state=None, complete_callback=None):
        """ Resume scheduler either after stopping (or silencing) """
        LOGGER.debug('Resuming Scheduler!')

        self._save_complete_callback = complete_callback

        if self._autopilot_present:
            if autopilot_state is None:
                autopilot_state = self._autopilot_state

            self.autopilot(autopilot_state)

        else:
            self._resume_scheduler()

            self._complete_callback()

    def silence_scheduler(self, complete_callback=None):
        """ Silences base scheduler """
        LOGGER.debug('Silencing Scheduler!')

        self._save_complete_callback = complete_callback

        if self._autopilot_present:
            if self._autopilot_state:
                self.bridge.base_node_ucast('smn__autopilot_notify', False)

            else:
                self._pause_scheduler()

        else:
            self._pause_scheduler()

        if not self._save_in_progress:
            self._complete_callback()

    def stop_scheduler(self, complete_callback=None):
        """ Stops Scheduler completely """
        LOGGER.debug('Stopping Scheduler!')

        self._save_complete_callback = complete_callback

        if self._autopilot_present:
            if self._autopilot_state:
                self.bridge.base_node_ucast('smn__autopilot', False)
                self.bridge.base_node_ucast('smn__autopilot_notify', False)

            else:
                self._pause_scheduler()

        else:
            self._pause_scheduler()

        if not self._save_in_progress:
            self._complete_callback()

    ## Private Methods ##
    # Sleepy Mesh Network States #
    def _sleep(self):
        """
        Periodic Sleep function
        Triggered after mcast sync has been performed (aka _sync method)
        Ucast Mode:
        _sync -> _sync_complete_handler -> _sleep
        Mcast Mode:
        _sync -> _mcast_sync -> _sync_complete_handler -> _sleep
        """
        if not self._autopilot_state:
            if not self._pause:
                # Calculated period minus sync processing timing
                calculated_period = self.sleep_period() - self.wake_period() / 2 - self._ct_ls()
                # LOGGER.debug('Awake Scheduled to ' + str(self._ct_ls() + calculated_period) + ' CT-LS')

                # Set scheduler to trigger _awake
                self.bridge.schedule(calculated_period, self._awake)

                # Change bridge polling mode
                self.bridge.set_polling_mode('sleep')

        return False

    def _awake(self):
        """
        Periodic Awake function
        Triggered by scheduler, scheduler set by _sleep function
        """
        if self._autopilot_state:
            self._mesh_awake = True
            self.__reset_flags()
            self.websocket.send(AWAKE, 'ws_awake')

        else:
            if not self._pause:
                self._mesh_awake = True

                self.__reset_flags()
                self._clear_sync_times()

                # Calculated period minus processing/error timing
                calculated_period = self.sleep_period() + self.wake_period() / 2 - self._ct_ls()
                # LOGGER.debug('Timeout Scheduled to ' + str(self._ct_ls() + calculated_period) + ' CT-LS')

                # Set scheduler to trigger timeout _sync
                # (alternatively _sync is triggered after all nodes checked in with the gate)
                self.bridge.schedule(calculated_period, self._sync)

                self.websocket.send(AWAKE, 'ws_awake')

                # Change bridge polling mode
                if self['data_in']['node_average'] is None:
                    self.bridge.set_polling_mode('awake')
                else:
                    self.bridge.set_polling_mode('awake', self['data_in']['node_average'] + SNAP_POLL_DEVIATION)

        return False

    # Sync Related Methods #
    def _sync(self, callback_type=None):
        """ Called either by successful sync or on timeout condition """
        if callback_type is None:
            callback_type = 'timeout'

        if self._autopilot_state:
            self._mesh_awake = False
            self._sync_type = callback_type
            SleepyMeshBase._update_last_sync(self)

            # Patch for now
            update_type = self.update_in_progress()
            if update_type == 'node_update':
                self._verify_updates()

        else:
            if not self._pause:
                if self._mesh_awake:
                    # Lock
                    self._mesh_awake = False

                    # Update last sync timing/statistics
                    self._update_last_sync(callback_type)

                    # Check if we need to execute any network updates
                    self._verify_updates()

                    # Send mcast to the network
                    self._mcast_sync()

        return False

    def _sync_complete_handler(self, *args):
        """ Callback for sync complete """
        # Find out type of sync
        packet_id = args[0]

        # LOGGER.debug('packet_id = ' + str(packet_id))
        # LOGGER.debug('self._mcast_sync_id = ' + str(self._mcast_sync_id))

        if self._mcast_sync_id == packet_id:
            # Put network to sleep state
            self._sleep()

            self._update_statistics_data()
            self.__update_nodes_data()
            self.__update_system_data()

            self.save()

            if not self._autopilot_state:
                # Do not refresh current web page if update is in progress
                if self.update_in_progress():
                    if self.update_in_progress('network_update'):
                        if self.bridge.check_base_node_reboot():
                            self.websocket.send(REBOOT_REQUEST, 'ws_init')

                    elif self.update_in_progress('virgin'):
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
    def _resume_scheduler(self):
        """ Restart Scheduler after software update """
        if self._pause:
            self._pause = False

            # LOGGER.debug("self._mesh_awake = " + str(self._mesh_awake))

            if self._mesh_awake:
                self._sync()
            else:
                self._awake()

        # Do not reschedule
        return False

    def _pause_scheduler(self):
        """ Pause Scheduler before software update """
        if not self._pause:
            self._pause = True

            self._clear_sync_times()

            # Just in case
            self.bridge.set_polling_mode('sleep')

        # Do not reschedule
        return False

    def _verify_updates(self):
        """ Check if we need to execute any network updates """
        network_ready = bool(self._sync_type != 'timeout')
        network_ready |= bool(len(self.platforms.select_nodes('active')) == 0)
        self.networks[0].verify_update(network_ready)

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
