"""
Common Node Utilities
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""


### INCLUDES ###
import logging

from py_knife.ordered_dict import OrderedDict

from gate.conversions import bin_to_int
from gate.database import DatabaseOrderedDict


### CONSTANTS ###
## Node Fields ##
NODE_UPDATE_FIELDS = ('name', 'live_enable', 'sensor_type')
# TO DO: ['firmware']                       # Snap Firmware
# NOT USED: ['mac', 'rGroup', 'fGroup']

## Network Fields ##
# NOTE: Make sure they correspond to structure fields
PRIMARY_NETWORK_FIELDS = ('channel', 'data_rate')
AES_FIELDS = ('aes_key', 'aes_enable')
CYCLE_FIELDS = ('wake', 'sleep')
TIMEOUT_FIELDS = ('timeout_wake', 'timeout_sleep')
RAW_CYCLES_FIELDS = (
    'wake_integer',
    'wake_remainder',
    'sleep_integer',
    'sleep_remainder'
)
RAW_TIMEOUT_FIELDS = (
    'timeout_wake_integer',
    'timeout_wake_remainder',
    'timeout_sleep_integer',
    'timeout_sleep_remainder'
)
NETWORK_FIELDS = PRIMARY_NETWORK_FIELDS + AES_FIELDS

BASE_NETWORK_FIELDS = NETWORK_FIELDS + CYCLE_FIELDS
NODE_NETWORK_FIELDS = NETWORK_FIELDS + TIMEOUT_FIELDS

# NOT USED: ('net_id', 'rGroup', 'fGroup')

## Update Defaults ##
NETWORK_UPDATE_FIELDS = NETWORK_FIELDS + CYCLE_FIELDS + TIMEOUT_FIELDS

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def parse_raw_data(raw_data):
    """ Parses raw data """
    raw_packet = None

    if raw_data is not None and len(raw_data):
        LOGGER.debug("Incoming raw_data len: " + str(len(raw_data)))
        if len(raw_data) >= 1:
            raw_packet_len = raw_data[:1]
            raw_data = raw_data[1:]

            packet_len = bin_to_int(raw_packet_len)
            LOGGER.debug("Packet length: " + str(packet_len))

            if packet_len is not None and len(raw_data) >= packet_len:
                raw_packet = raw_data[:packet_len]
                raw_data = raw_data[packet_len:]

            else:
                del raw_data[:]

        if raw_packet is None:
            LOGGER.warning("Dropping the rest of the data length of '" + str(len(raw_data)) + "'!")

    return raw_packet, raw_data


### CLASSES ###
class UpdateDict(DatabaseOrderedDict):
    """ Dictionary to store requested update values """
    def __init__(self, update_keys):
        defaults = OrderedDict()
        for key in update_keys:
            defaults[key] = None

        super(UpdateDict, self).__init__(defaults=defaults)

    def update(self, update_dict):
        """ Update only existing keys, drop the rest """
        for field in self.keys():
            if field in update_dict.keys():
                self[field] = update_dict[field]

    def compare(self, compare_dict):
        """ Compares update dictionary values """
        for field in self.keys():
            if field in compare_dict.keys():
                if self[field] is not None:
                    if self[field] == compare_dict[field]:
                        # Update was successful
                        self[field] = None

        return self

    def reset(self):
        """ Resets dictionary """
        for field in self.keys():
            self[field] = None
