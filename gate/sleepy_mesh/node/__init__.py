"""
Node Class
Establishes sub class hierarchy, defines external methods (most important ones..)
"""

### INCLUDES ###
import copy
import logging

from hw_platform import NodePlatform
from headers import DIAGNOSTIC_FIELDS
from header_mixin import HeaderMixin


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Node(NodePlatform, HeaderMixin):
    ## Public Methods ##
    def update_last_sync(self, last_sync):
        """ Updates last sync variable """
        if self['presence']:
            self.update({'last_sync': last_sync})

    def update_logs(self):
        """ Append logs (if needed). Dump logs to a file (if needed). Return dump log flag """
        if self['log_enables'] and self['new_data']:
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

    # Header Related Methods #
    def read_headers(self, header_type):
        output = {}

        if self.headers is not None:
            output = self.headers.read(header_type, self['sensor_type'])

        return output

    def raw_enables(self, set_value=None):
        """ Reads/Sets raw_enables using header enables """
        enable_value = 0

        all_headers = self.read_headers('all')
        for header in all_headers.values():
            if header['data_field_position'] is not None:
                raw_mask = 1 << header['data_field_position']

                live_enable = header.enables(self, 'live_enables')
                diag_enagle = header.enables(self, 'diag_enables')
                header_enable = live_enable or diag_enagle

                # Write
                if set_value is not None:
                    raw_enable = bool(set_value & raw_mask)
                    if raw_enable != header_enable:
                        header_enable = raw_enable

                        header.enables(self, 'live_enables', raw_enable)
                        if not raw_enable:
                            header.enables(self, 'diag_enables', raw_enable)

                # Read
                if header_enable:
                    enable_value |= raw_mask

        return enable_value

    def network_preset_needed(self):
        """ Determines if the node needs network preset performed """
        output = not self['network_preset']
        output &= not self['inactive']
        output &= self['type'] == 'node'

        return output
