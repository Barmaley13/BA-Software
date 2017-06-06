"""
Sleepy Mesh Network Portion
"""

### INCLUDES ###
import logging

from gate import conversions

from statistics import SleepyMeshStatistics
from networks import NETWORK_UPDATE_TYPES


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class SleepyMeshNetwork(SleepyMeshStatistics):
    # Methods for Overloading #
    def _sync(self, callback_type='timeout'):
        """ Blank method should be overwritten by a parent class """
        LOGGER.error("Method _sync is not implemented!")
        raise NotImplementedError

    # Bridge to Gate Methods #
    def _callback(self, callback_type, *args):
        """ Called by nodes """
        # Note start time for the metrics
        start = self._ct_ls()
        self._log_sync_start_time(start)

        node = self.networks[0].callback(callback_type, *args)

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
            node['off_sync'] = True

        return not self._mesh_awake
