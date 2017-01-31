"""
Sleepy Mesh Network Portion
"""

### INCLUDES ###
import logging

from gate import conversions

from statistics import SleepyMeshStatistics
from networks import NETWORK_UPDATE_TYPES


### CONSTANTS ###
## Strings ##
OFF_SYNC = "Off Sync: "

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class SleepyMeshNetwork(SleepyMeshStatistics):
    def __init__(self, **kwargs):
        super(SleepyMeshNetwork, self).__init__(**kwargs)

        # Internal Members #
        self._pause = False

        self._mcast_sync_id = None
        self._ucast_sync_id = None

    ## Public/Private Methods ##
    # Gate to Bridge Methods #
    def _mcast_sync(self):
        """ Send multi cast to network in order to sync (and sleep) """
        calculated_period = self.sleep_period() - self._ct_ls()
        if self._delay_average is not None:
            calculated_period -= self._delay_average
        sync_args = conversions.get_int_rem(calculated_period)
        # LOGGER.debug('MCAST Sync Period :' + str(calculated_period) + ' seconds')

        self._mcast_sync_id = self.bridge.network_mcast('smn__sync', *sync_args)
        # LOGGER.debug('self._mcast_sync_id: ' + str(self._mcast_sync_id))

    def _ucast_sync(self, net_addr, sleep_period=None):
        """
        Send uni cast sync to particular node.
        Used to sync nodes that are off sync or manual sync during network update
        """
        if sleep_period is None:
            # sleep_period = self.sleep_period()
            sleep_period = self.sleep_period() * 2 + self.wake_period() / 2 - self._ct_ls()

        if self._delay_average is not None:
            sleep_period -= self._delay_average
        LOGGER.debug(str(net_addr) + ' sync period: ' + str(sleep_period))

        sync_args = conversions.get_int_rem(sleep_period)
        if sync_args[0] or sync_args[1]:
            self._ucast_sync_id = self.bridge.network_ucast(net_addr, 'smn__sync', *sync_args)

    # Methods for Overloading #
    def _sync(self, callback_type='timeout'):
        """ Blank method should be overwritten by a parent class """
        LOGGER.error("Method _sync is not implemented!")
        raise NotImplementedError

    # Bridge to Gate Methods #
    def _callback(self, callback_type, *args):
        """ Called by nodes """
        if not self._pause:
            # Note start time for the metrics
            start = self._ct_ls()
            self._log_sync_start_time(start)

            node, mcast_sync = self.networks[0].callback(callback_type, *args)

            if node is not None:
                off_sync_node = self.__check_off_sync(node)

                # Note end time for the metrics
                stop = self._ct_ls()
                self._log_node_processing_time(node, start, stop)

                # Perform Syncing Procedures
                if not off_sync_node:
                    self._sync(callback_type)

            # Check for the next incoming message
            self.bridge.poll_snap()

    ## Class-Private Methods ##
    def __check_off_sync(self, node):
        """ Checks if node is off sync. Syncs it if needed """
        if not self._mesh_awake and not node['off_sync']:
            # Eliminate off sync messaging repeats
            node['off_sync'] = True

            catch_up_time = self.sleep_period() - self._ct_ls()
            if self._delay_average is not None:
                catch_up_time -= self._delay_average

            if catch_up_time > 0:
                # Protect from max
                if catch_up_time > conversions.TIMEOUT_MAX_FLOAT:
                    catch_up_time = conversions.TIMEOUT_MAX_FLOAT

                self._ucast_sync(node['net_addr'], catch_up_time)

                self.websocket.send(OFF_SYNC + node['net_addr'] + self._ct_ls_str())

        return not self._mesh_awake
