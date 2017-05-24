"""
Some common code for the Sleepy Mesh module
"""

### INCLUDES ###
import logging

from py_knife.ordered_dict import OrderedDict

from gate.conversions import bin_to_hex, bin_to_int, get_float, get_base_float
from gate.database import DatabaseOrderedDict


### CONSTANTS ###
## Node Fields ##
NODE_UPDATE_FIELDS = ('name', 'live_enable')
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

## Callback Arguments ##
SHORT_LOG_FIELDS = ('raw_net_addr', 'name', 'raw_enables', 'raw_data', 'raw_lq', 'raw_error')
LONG_LOG_FIELDS = ('name', 'raw_mac', 'raw_platform', 'firmware', 'software', 'raw_error')
PRIMARY_NETWORK_LOG_FIELDS = ('raw_net_addr', ) + NETWORK_FIELDS
NETWORK_LOG_FIELDS = PRIMARY_NETWORK_LOG_FIELDS + RAW_TIMEOUT_FIELDS
BASE_LOG_FIELDS = PRIMARY_NETWORK_LOG_FIELDS + RAW_CYCLES_FIELDS

## Callback Fields Map ##
CALLBACK_FIELDS_MAP = {
    'long': LONG_LOG_FIELDS,
    'short': SHORT_LOG_FIELDS,
    'network': NETWORK_LOG_FIELDS,
    'base': BASE_LOG_FIELDS
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def network_preset_needed(node):
    """ Determines if the node needs network preset performed """
    output = not node['network_preset'] and node['type'] == 'base'
    output |= not node['network_preset'] and not node['inactive']
    return output


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


def parse_callback_data(raw_dict):
    """ Convert raw mac or network address """
    # Generic Fields #
    if 'raw_mac' in raw_dict:
        # raw_net_addr = raw_mac[5:8]
        raw_dict['mac'] = bin_to_hex(raw_dict['raw_mac'])
        raw_dict['net_addr'] = raw_dict['mac'][10:16]
        del raw_dict['raw_mac']

    elif 'raw_net_addr' in raw_dict:
        raw_dict['net_addr'] = bin_to_hex(raw_dict['raw_net_addr'])
        del raw_dict['raw_net_addr']

    # Short/Long Log Fields #
    if 'name' in raw_dict:
        # Protect name from None value
        if raw_dict['name'] is None:
            raw_dict['name'] = ""

    if 'raw_platform' in raw_dict:
        raw_dict['raw_platform'] = raw_dict['raw_platform'].lower()

    for field in ('raw_enables', 'raw_lq', 'raw_error') + RAW_CYCLES_FIELDS + RAW_TIMEOUT_FIELDS:
        if field in raw_dict and type(raw_dict[field]) not in (int, long):
            # LOGGER.debug("Overwriting field: " + str(field))
            raw_dict[field] = bin_to_int(raw_dict[field])
            # LOGGER.debug('raw_dict[field]: ' + str(raw_dict[field]))

    if 'raw_enables' in raw_dict:
        # Note: 'live_enable' is required for parsing data
        raw_dict['live_enable'] = raw_dict['raw_enables']
        del raw_dict['raw_enables']

    # Network Log Fields #
    network_fields = CYCLE_FIELDS + TIMEOUT_FIELDS
    for field in network_fields:
        field_integer = field + '_integer'
        field_remainder = field + '_remainder'

        if field_integer in raw_dict and field_remainder in raw_dict:
            _get_float = get_float
            if field in CYCLE_FIELDS:
                _get_float = get_base_float

            raw_dict[field] = _get_float(raw_dict[field_integer], raw_dict[field_remainder])
            del raw_dict[field_integer]
            del raw_dict[field_remainder]

    return raw_dict


def get_input_dict(callback_type, *callback_args):
    """ Convert callback_args to dictionary format """
    output = None

    if callback_type in CALLBACK_FIELDS_MAP:
        fields = CALLBACK_FIELDS_MAP[callback_type]
        if len(fields) == len(callback_args):
            raw_dict = dict(zip(fields, callback_args))

            LOGGER.debug('callback_type:' + str(callback_type))
            LOGGER.debug('raw_dict:' + str(raw_dict))

            output = parse_callback_data(raw_dict)

    return output


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
