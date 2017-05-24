"""
Sleepy Mesh Base Class
"""


### INCLUDES ###
import logging

from gate.database import DatabaseDict
from gate.update_interface import UpdateInterfaces
from gate.modbus import ModbusServer
from gate.snmp import SNMPTrapServer

from error import BaseError, NodeError
from bridge import Bridge
from uploader import Uploader
from nodes import Nodes
from platforms import Platforms
from networks import Networks


### CONSTANTS ###
## Sleepy Mesh Sync Types ##
SYNC_TYPES = {
    'timeout': 'Timeout',
    'short': 'Short Log',
    'long': 'Long Log'
}

## Last Syncs Constants ##
LAST_SYNCS_NUMBER = 2

## Dynamic Wake Period ##
DYNAMIC_WAKE_PERIOD = True
SYNC_DEVIATION = 0.100              # seconds

## Strings ##
CT_LS = "! CT-LS: "

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class SleepyMeshBase(DatabaseDict):
    def __init__(self, system_settings, websocket, snmp_websocket, **kwargs):
        super(SleepyMeshBase, self).__init__(**kwargs)

        if 'last_syncs' not in self._defaults:
            self._defaults.update({
                'last_syncs': list()
            })

        # Internal Members #
        self._mesh_awake = True
        self._sync_type = 'timeout'

        self._save_in_progress = False

        self._sync_average = None
        self._delay_average = None

        # Instances #
        # TODO: Eliminate as many dependencies as possible
        self.system_settings = system_settings
        self.websocket = websocket
        self.snmp_websocket = snmp_websocket

        self.modbus_server = ModbusServer()
        self.snmp_server = SNMPTrapServer(self)
        self.update_interfaces = UpdateInterfaces(self)
        self.update_in_progress = self.update_interfaces.update_in_progress

        self.bridge = Bridge(self.system_settings)
        self.uploader = Uploader(self)

        self.nodes = Nodes(self.system_settings)
        self.platforms = Platforms(self.nodes)
        self.networks = Networks(self)

        self.error = BaseError(self.system_settings)

        if self.system_settings.modbus_enable:
            system_settings_dict = self.system_settings.attr_dict()
            # LOGGER.debug('Modbus Attribute Dictionary: ' + str(system_settings_dict))
            self.modbus_server.start(system_settings_dict)

        if self.system_settings.snmp_enable:
            self.snmp_server.start()

            # Overload Node Error Methods (SNMP Error Methods)#
            NodeError.send_snmp = self.snmp_server.send_snmp
            NodeError.clear_snmp = self.snmp_server.clear_snmp

    ## Public/Private Methods ##
    # Sleep/Wake Period Methods #
    def sleep_period(self):
        """ Fetches sleep period """
        return self.networks[0]['sleep']

    def _wake_period(self):
        """ Fetches wake period """
        return self.networks[0]['wake']

    def wake_period(self):
        """ Fetches wake period (or dynamic wake period if enabled) """
        static_wake_period = self._wake_period()
        output = static_wake_period

        if DYNAMIC_WAKE_PERIOD:
            if self._sync_average is not None:
                dynamic_wake_period = self._sync_average + SYNC_DEVIATION

                if dynamic_wake_period < static_wake_period:
                    output = dynamic_wake_period

        return output

    def save(self, db_content=None):
        """ Overloading default save method """
        self._save_in_progress = True

        # Save statistics data
        super(SleepyMeshBase, self).save(db_content)

        self.platforms.save()

        if self.system_settings.modbus_enable:
            self.modbus_server.save()

        if self.system_settings.snmp_enable:
            self.snmp_server.save()

        self._save_in_progress = False

    ## Private Methods ##
    # Last Sync Related Methods #
    def _update_last_sync(self):
        """ Updates last sync """
        last_sync = self.system_settings.time()
        self['last_syncs'].append(last_sync)
        if len(self['last_syncs']) > LAST_SYNCS_NUMBER:
            del self['last_syncs'][0]

    def _ct_ls(self):
        """ Returns current system time - last sync value """
        output = 0
        if len(self['last_syncs']):
            output = self.system_settings.time() - self['last_syncs'][-1]

        return output

    def _ct_ls_str(self, ct_ls=None):
        """ Returns current system time - last sync string """
        if ct_ls is None:
            ct_ls = self._ct_ls()

        output = CT_LS + "{0:.3f}".format(ct_ls)

        return output
