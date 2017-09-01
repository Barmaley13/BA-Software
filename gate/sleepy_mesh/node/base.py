"""
Single Node related intricacies
"""

### INCLUDES ###
import os
import copy
import logging
from distutils.version import StrictVersion

from gate.conversions import find_version
from gate.database import DatabaseDict
from gate.sleepy_mesh import error

from common import NODE_UPDATE_FIELDS, NETWORK_UPDATE_FIELDS, UpdateDict
from headers import generate_node_headers, generate_sensor_types
from logs import NodeLogs


### CONSTANTS ###
MCAST_TIMEOUT_THRESHOLD = 3


## Node Defaults ##
# TODO: Create dynamic mechanism to display node fields
# Hint: Use special key strings, i.e. "Name" instead of "name"
# TODO: Move field initialization that does not belong here somewhere else!
NODE_DEFAULTS = {
    # Used by node, virgins, bridge
    'name': None,               # read
    'mac': None,                # read
    'net_addr': None,           # read
    'modbus_addr': None,        # read/write
    'raw_platform': None,       # read
    'raw_enables': None,        # read
    'firmware': None,           # read
    'software': None,           # read

    # Used only by node
    'live_enables': 0,          # internal (used by header indirectly)
    'log_enables': 0,           # internal (used by header indirectly)
    'diag_enables': 0,          # internal (used by header indirectly)
    'presence': False,          # read/(write only virgins)
    # Tells if system waits for this node to respond during each sync
    'mcast_presence': True,     # internal
    'mcast_timeout': 0,         # internal

    # Used by PLATFORMS, created dynamically!
    'platform': None,           # read (used by platforms)
    'group': None,              # read (used by platforms)

    # Used by network
    'net_verify': False,
    'off_sync': False,
    'off_sync_time': None,
    # Tells if this node is part of the inactive (uninitialized) group
    'inactive': True,           # read/write

    # Some Update Flags
    'network_preset': False,
    'software_update': False,
    # Signalizes the need to reset nv parameters after uploading new software on a node
    'post_software_update': False,

    # Used by uploader (network)
    'type': 'node'
}

## Minimum Firmware/Software Versions ##
MIN_FIRMWARE_VERSION = '2.7.1'
MIN_SOFTWARE_VERSION = '2.22'

MIN_VERSION_MAP = {
    'firmware': MIN_FIRMWARE_VERSION,
    'software': MIN_SOFTWARE_VERSION,
}

MIN_VERSION_ERROR_MAP = {
    'firmware': error.OLD_FIRMWARE,
    'software': error.OLD_SOFTWARE,
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class NodeBase(DatabaseDict):
    """ Generic Node class """
    def __init__(self, system_settings, input_dict):
        # Public Members #
        self.system_settings = system_settings

        # Create Headers
        self.headers = None
        if 'raw_platform' in input_dict:
            self.headers = generate_node_headers(input_dict['raw_platform'])
            self.headers.refresh(self, reverse=True)
            input_dict['sensor_type'] = generate_sensor_types(input_dict['raw_platform'])

        node_defaults = {}
        if self.headers is not None:
            header_defaults = copy.deepcopy(self.headers.header_defaults)
            node_defaults.update(header_defaults)

        node_defaults.update(copy.deepcopy(NODE_DEFAULTS))
        if input_dict is not None:
            node_defaults.update(input_dict)

        # Append defaults with time stamps
        current_time = self.system_settings.time()
        node_defaults.update({'created': current_time, 'last_sync': current_time})

        db_file = None
        error_db_file = None
        if node_defaults['net_addr'] is not None and node_defaults['type'] == 'node':
            db_file = os.path.join('nodes', node_defaults['net_addr'] + '.db')
            logs_db_file = os.path.join('nodes', 'logs', node_defaults['net_addr'] + '.db')
            error_db_file = os.path.join('nodes', 'error', node_defaults['net_addr'] + '.db')

            self.logs = NodeLogs(
                name=node_defaults['net_addr'],
                system_settings=self.system_settings,
                db_file=logs_db_file
            )

        else:
            self.logs = None

        super(NodeBase, self).__init__(
            db_file=db_file,
            defaults=node_defaults
        )

        # Load Headers
        if self.headers is None and self['type'] == 'node':
            if 'raw_platform' in self._main:
                self.headers = generate_node_headers(self['raw_platform'])
                self.headers.refresh(self)

        self.update_dict = UpdateDict(NODE_UPDATE_FIELDS + NETWORK_UPDATE_FIELDS)
        self.error = error.NodeError(system_settings=self.system_settings, db_file=error_db_file)

        # Overloaded Error Methods #
        # FIXME: More elegant way to do this?
        old_set_error = self.error.set_error

        def new_set_error(*args, **kwargs):
            """ Overloading set_error to automatically generate error_messages for the nodes """
            _set_error_args = error.set_error_args(self, *args, **kwargs)
            old_set_error(*_set_error_args)

        self.error.set_error = new_set_error

        # Detect old firmware/software during node creation
        self.__detect_old_versions(input_dict)

    ## Public Methods ##
    def reset_flags(self):
        """
        Sets presence and off_sync flags to False. As well as mcast presence.
        Bridge fulfils networking function. This is just for user reference.
        :return: NA
        """
        # Update active & timeout flags #
        # Not present?
        if not self['presence']:
            # Mcast Sync Present?
            if self['mcast_presence']:
                self['mcast_timeout'] += 1
                self['mcast_presence'] = not bool(self['mcast_timeout'] > MCAST_TIMEOUT_THRESHOLD)

        # Reset flags #
        self['presence'] = False
        self['off_sync'] = False
        self['new_data'] = False

    def update(self, update_dict):
        """ Overloading Base Update Method """
        self.__set_flags()

        if 'sensor_type' in update_dict:
            if self['sensor_type'] != update_dict['sensor_type']:
                self.headers.rename_headers(update_dict['sensor_type'])

        if 'raw_error' in update_dict:
            self.__update_error(update_dict['raw_error'])
            del update_dict['raw_error']

        self.__detect_old_versions(update_dict)

        super(NodeBase, self).update(update_dict)

    ## Class-Private Methods ##
    def __set_flags(self):
        """ Set presence related flags """
        self['presence'] = True
        self['mcast_presence'] = True
        self['mcast_timeout'] = 0

        self.error.clear_error('generic', error.ABSENT_NODE)

    def __update_error(self, raw_error):
        if not self['inactive']:
            for error_code in error.NODE_MESSAGES.keys():
                error_mask = 1 << error_code
                if raw_error & error_mask:
                    self.error.set_error('node_fault', error_code)
                else:
                    self.error.clear_error('node_fault', error_code)

            if raw_error:
                self.error.set_error('generic', error.HW_ERROR)
            else:
                self.error.clear_error('generic', error.HW_ERROR)

    def __detect_old_versions(self, update_dict):
        """ Detects old versions of either software or firmware """
        for ware_type in ('firmware', 'software'):
            if ware_type in update_dict:
                current_version_str = find_version(update_dict[ware_type])
                min_version_error = MIN_VERSION_ERROR_MAP[ware_type]

                if not len(current_version_str):
                    self.error.set_error('generic', min_version_error)

                else:
                    current_version = StrictVersion(current_version_str)
                    min_version = StrictVersion(find_version(MIN_VERSION_MAP[ware_type]))

                    if current_version < min_version:
                        self.error.set_error('generic', min_version_error)

                        LOGGER.debug('Current {} version: {}'.format(ware_type, current_version))
                        LOGGER.debug('Min {} version: {}'.format(ware_type, min_version))

                    else:
                        self.error.clear_error('generic', min_version_error)
