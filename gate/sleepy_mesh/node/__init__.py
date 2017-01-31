"""
Node Class
Establishes sub class hierarchy, defines external methods (most important ones..)
"""

### INCLUDES ###
import copy
import logging

from hw_platform import NodePlatform
from data import ADC_FIELDS
from diagnostics import DIAGNOSTIC_FIELDS


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Node(NodePlatform):
    ## Public Methods ##
    def update_last_sync(self, last_sync):
        """ Updates last sync variable """
        if self['presence']:
            self.update({'last_sync': last_sync})

    def update_logs(self):
        """ Append logs (if needed). Dump logs to a file (if needed). Return dump log flag """
        if self['log_enable'] and self['new_data']:
            log_data = copy.deepcopy(self['data_out'])
            log_data['time'] = self['last_sync']
            self.logs.append(log_data)

        return self.logs.dump()

    # Time Related Methods #
    def update_timing(self, time_diff):
        """ Updates node timing """
        # Update internal timing (created and logs fields)
        self['created'] += time_diff
        self['last_sync'] += time_diff
        self.logs.update_timing(time_diff)

    def last_sync(self):
        """ Reports time of the node's last sync """
        return self.system_settings.local_time(self['last_sync'])

    def created(self):
        """ Reports time of the node creation """
        return self.system_settings.local_time(self['created'])
