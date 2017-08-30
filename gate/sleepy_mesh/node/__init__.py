"""
Node Class
Establishes sub class hierarchy, defines external methods (most important ones..)
"""

### INCLUDES ###
import copy
import logging

from hw_platform import NodePlatform
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
        # self['log_enable'] = self.generate_enables('log_enable')
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

    # Header Related Methods #
    def read_headers(self, header_type):
        output = {}

        if self.headers is not None:
            output = self.headers.read(header_type, self['sensor_type'])

        return output

    def generate_enables(self, enable_type, overwrite_headers=False):
        """ Generates node enables from header enables """
        enable_value = 0

        if enable_type in ('live_enable', 'log_enable', 'diagnostics'):
            # Convert to node enables
            all_headers = self.read_headers('all').values()
            for header in all_headers:
                if header['data_field_position'] is not None:
                    header_mask = 1 << header['data_field_position']
                    if overwrite_headers:
                        header_enable = (self[enable_type] & header_mask) > 0
                        header.enables(self, enable_type, header_enable)

                    if header.enables(self, enable_type):
                        enable_value |= header_mask

            # LOGGER.debug("{} = {}".format(enable_type, enable_dict))
            # LOGGER.debug("enable_value = ".format(enable_value))

        else:
            LOGGER.error("Enable type '{}' does not exist!".format(enable_type))

        return enable_value

    def update_enables(self, enable_type, enable_dict):
        """ Updates header enables using enable_dict. AKA User update. """
        enable_value = 0

        if enable_type in ('live_enable', 'log_enable', 'diagnostics'):
            # Convert to node enables
            all_headers = self.read_headers('all')
            for header in all_headers.values():
                header_mask = None
                if header['data_field_position'] is not None:
                    header_mask = 1 << header['data_field_position']

                if header['internal_name'] in enable_dict:
                    bit_value = enable_dict[header['internal_name']]
                    # Compose node enables
                    if bit_value is not None and header_mask is not None:
                        if bit_value:
                            enable_value |= header_mask

                        else:
                            enable_value |= self[enable_type] & header_mask

                    # Update headers
                    if bit_value is not None:
                        header.enables(self, enable_type, bit_value)

            # LOGGER.debug("{} = {}".format(enable_type, enable_dict))
            # LOGGER.debug("enable_value = ".format(enable_value))

        else:
            LOGGER.error("Enable type '{}' does not exist!".format(enable_type))

        return enable_value

    def network_preset_needed(self):
        """ Determines if the node needs network preset performed """
        output = not self['network_preset']
        output &= not self['inactive']
        output &= self['type'] == 'node'

        return output
