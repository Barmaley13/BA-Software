"""
Bridge Module contains Bridge Class. Bridge Class is responsible for:

    * Initializing internal scheduler
    * Creating Snap Connect communication instance
    * Initializing that instance by setting default and AES network NV parameters
    * Pulling initial data off of base node
    * Some support methods that uploader and virgins classes are using
    * Base node reboot methods
    * Callbacks methods that are mapped to SnapPy functions
    * Network messaging methods such as unicasts, multicasts and etc

Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import time
import copy
import glob
import logging

from distutils.version import StrictVersion
from tornado import ioloop, autoreload
from apy import ioloop_scheduler
from snapconnect import snap

from py_knife import platforms, com_port

from gate.conversions import hex_to_bin
from gate.sleepy_mesh.common import AES_FIELDS
from gate.sleepy_mesh.node import Node

# Imports from Snap Connect Tornado Example #
# Monkey Patch so APY is happy with stock Tornado
if StrictVersion(snap.VERSION) >= StrictVersion('3.2.0'):
    ioloop.IOLoop.time_func = time.time
else:
    ioloop.IOLoop.timefunc = time.time

# Monkey Patch so Tornado does NOT auto reload the python modules in debug mode,
# because it messes up Snap Connect, and we really just want JS/Template reloads.
autoreload.start = lambda x = None, y = None: (x, y)

### CONSTANTS ###
# NOTE: Too frequent poll will choke up everything. Too long poll will slow down system response/sync
# Might want to experiment at some point to find out the best poll value.
SNAP_POLL_DEVIATION = 0.005         # s
_SNAP_AWAKE_POLL = 25               # ms
_SNAP_SLEEP_POLL = 100              # ms

## Sleepy Mesh Mcast Messaging Constants ##
MCAST_GROUP = 1
MCAST_TTL = 3

## Network Address Size ##
NET_ADDR_STR_SIZE = 6  # Bytes

# Default Request Template #
DEFAULT_REQUEST = {
    # Requested SnapPy function as a string
    'request': None,
    # Reference to place holder that will be filled once the request value is received
    'reference': None,
    'reference_key': None,
    # Description of the requested data if you would like to print it to the screen
    'description': None,
    # Post processing function (make sure it will work with current implementation)
    'post_processing': None,
    # External Callback Routine to notify that request has been fulfilled
    'callback': None
}

## NV Map ##
AES_NV_MAP = {
    'aes_key': snap.NV_AES128_KEY_ID,
    'aes_enable': snap.NV_AES128_ENABLE_ID
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Bridge(object):
    """ Bridge class that manages all communications with Snap Connect """

    def __init__(self, system_settings):
        """
        Create instance of a Bridge Class
        :return: Bridge instance
        """
        # Communication Nodes #
        self.gate = Node(
            system_settings=system_settings,
            input_dict={
                'name': 'Gate',
                'presence': True,
                'inactive': False,
                'type': 'gate',
            }
        )
        self.base = Node(
            system_settings=system_settings,
            input_dict={
                'name': 'Base',
                'presence': True,
                'channel': None,
                'inactive': False,
                'type': 'base',
            }
        )

        # Internal Variables #
        self._bridge_init_info = None
        self._requests = list()
        self._base_node_reboot_flag = False
        self._vm_stat_callback = None

        self._serial_args = list()

        # Init Procedure #
        # Create SNAP Connect instance. Note: we are using Tornado scheduler.
        self._scheduler = ioloop_scheduler.IOLoopScheduler.instance()

        self.com = snap.Snap(scheduler=self._scheduler, funcs={})
        # Set Tornado scheduler to call SNAP Connect's internal poll function.
        # Tornado already polls asyncore.
        # self._poll_timer = ioloop.PeriodicCallback(self._poll_snap, _SNAP_AWAKE_POLL)
        self._poll_timer = ioloop.PeriodicCallback(self._poll_snap, _SNAP_SLEEP_POLL)

    ## Init Methods ##
    def init(self, bridge_init_info):
        """
        Initialize bridge

        :param bridge_init_info: Please refer to Manager.start method for the example
        :return: NA
        """
        self._bridge_init_info = bridge_init_info
        self._open_snap_connection()

    def _post_init(self):
        """
        Post Init procedure

        :return: NA
        """
        self._set_default_nv_parameters()
        self.set_aes_nv_parameters(self._bridge_init_info['init_nv_param'])

        # Note: Initialized here for proper initializing moment
        self.com.set_hook(snap.hooks.HOOK_RPC_SENT, self._bridge_init_info['sync_complete_handler'])

        # Set GATE Address (for Dynamic Addressing)
        self.base_node_ucast('smn__set_gate_addr')

        # Fetch initial data
        self.add_callbacks(self._bridge_init_info['pre_init_callbacks'])
        self.refresh_info(self._init_complete)

    def _init_complete(self):
        """
        Finish init procedure

        :return: NA
        """
        if self.gate['net_addr'] is not None:
            # Add the rest of the callbacks
            self.add_callbacks(self._bridge_init_info['post_init_callbacks'])
            self._bridge_init_info['init_complete_handler']()

    ## Refresh Info Methods ##
    def refresh_info(self, callback=None):
        """
        Refresh bridge related info.
        This function fetches information from gate node (Snap Connect Instance) and base node.
        Uses provided earlier bridge initialization information to fill out requests related data.

        :param callback: Function to call once this process is done
        :return: NA
        """
        # LOGGER.debug('Sending Refresh Info to Bridge!')

        for raw_request in self._bridge_init_info['requests']:
            self._requests.append(copy.deepcopy(DEFAULT_REQUEST))
            self._requests[-1].update(raw_request)

        self._requests[-1]['callback'] = callback

        # Trigger first request
        self.base_node_ucast('callback', 'brg__request', self._requests[0]['request'])

        # Do not reschedule
        return False

    def base_node_request_callback(self, *args):
        """
        This callback is executed when requested data is received.
        Basically, it uses request data to fill in the blanks,
        post process data (if enabled), print data (if enabled)
        and call external callback routine (if enabled)

        :param args: Data that has been requested
        :return: NA


        .. note:: args are not passed as part of the external callback at the moment
        """
        value = args[0]

        if len(self._requests):
            if self._requests[0]['post_processing'] is not None:
                value = self._requests[0]['post_processing'](value)

            if self._requests[0]['reference'] is not None:
                reference_dicts = self._requests[0]['reference']
                if type(reference_dicts) not in (list, tuple):
                    reference_dicts = [reference_dicts]

                reference_key = self._requests[0]['reference_key']

                for reference_dict in reference_dicts:
                    # LOGGER.debug('type(reference_dict[reference_key]) = ' + str(type(reference_dict[reference_key])))
                    # LOGGER.debug('type(value) = ' + str(type(value)))

                    if reference_dict[reference_key] is None or type(reference_dict[reference_key]) == type(value):
                        reference_dict[reference_key] = value

                if self._requests[0]['description'] is not None:
                    print self._requests[0]['description'] + str(reference_dicts[-1][reference_key])

            if self._requests[0]['callback'] is not None:
                # Do not pass args
                self._requests[0]['callback']()
                # Do pass args
                # self._requests[0]['callback'](*args)

            del self._requests[0]

        # Trigger next request
        if len(self._requests):
            self.base_node_ucast('callback', 'brg__request', self._requests[0]['request'])

    ## Start/Stop Methods ##
    def _open_snap_connection(self):
        """
        Starts Snap Connect

        :return: NA
        """
        # Open serial connection to Base node #
        if self.gate['net_addr'] is None:
            self._stop_snap_connection()

            if not len(self._serial_args):
                # E10
                if platforms.PLATFORM == platforms.SYNAPSE_E10:
                    serial_types = [snap.SERIAL_TYPE_RS232]
                    serial_ports = ['/dev/ttyS1']

                # Windows
                elif platforms.PLATFORM == platforms.WINDOWS:
                    serial_types = [snap.SERIAL_TYPE_SNAPSTICK100, snap.SERIAL_TYPE_SNAPSTICK200]
                    serial_ports = [0]

                # Others
                else:
                    serial_types = [snap.SERIAL_TYPE_RS232, snap.SERIAL_TYPE_SNAPSTICK200]
                    serial_ports = com_port.available_ports()

                # Raspberry Pi (add more serial ports)
                if platforms.PLATFORM == platforms.RASPBERRY_PI:
                    rpi3_devices = glob.glob('/dev/serial*')
                    serial_ports = serial_ports + rpi3_devices

                for serial_type in serial_types:
                    for serial_port in serial_ports:
                        self._serial_args.append((serial_type, serial_port))

                LOGGER.debug('Serial Args: ' + str(self._serial_args))

            serial_args = None
            while len(self._serial_args):
                serial_args = self._serial_args.pop(0)
                try:
                    self.com.open_serial(*serial_args)
                    LOGGER.debug('Connected: ' + str(serial_args))
                    break
                except:
                    serial_args = None
                    continue
            else:
                LOGGER.error('Could not connect to a bridge node!')

            self._poll_timer.start()
            self.schedule(3.0, self._open_snap_connection)

            if serial_args is not None:
                self._post_init()

        return False

    def _stop_snap_connection(self):
        """
        Stops Snap Connect

        :return: NA

        .. note:: Not used at the moment. Kept for future use/reference
        """
        self.com.close_all_serial()
        self._poll_timer.stop()

    ## NV Parameters Methods ##
    def _set_default_nv_parameters(self):
        """
        Sets some default NV parameters. Scheduler timer was messed up without
        call to this function due to route refresh or something like that.

        :return: NA
        """
        # Lock down our routes (we are a stationary device)
        self.com.save_nv_param(snap.NV_MESH_ROUTE_AGE_MAX_TIMEOUT_ID, 0)
        # Setup groups
        self.com.save_nv_param(snap.NV_GROUP_INTEREST_MASK_ID, 0xFFFF)
        self.com.save_nv_param(snap.NV_GROUP_FORWARDING_MASK_ID, 0xFFFF)
        # Allow others to change our NV Parameters
        self.com.save_nv_param(snap.NV_LOCKDOWN_FLAGS_ID, 0)

    def set_aes_nv_parameters(self, nv_dict):
        """
        Sets AES NV Parameters
        Make sure to perform this before talking to base node if AES is set

        :param nv_dict: Dictionary containing 'aes_key' and 'aes_enable' values
        :return: NA
        """
        ## AES Settings ##
        for field in AES_FIELDS:
            if field in nv_dict and field in AES_NV_MAP:
                self.com.save_nv_param(AES_NV_MAP[field], nv_dict[field])
            else:
                LOGGER.error("Can not find following field: " + str(field) + " in the provided nv_dict")

        # Debugging
        print "AES Key: " + str(nv_dict['aes_key'])
        print "AES: " + str(nv_dict['aes_enable'])

    ## SNAP Support Methods (Required for uploader and virgins) ##
    def set_vm_stat_callback(self, callback=None):
        """
        This function determines behavior of :func:`.tell_vm_stat` method

        :param callback: if None pass args to Snap Connect spy_upload_mgr
            that I don't know anything about. Uploader uses that mode.
            If callback set, pass value of the response to the specified callback.
            Virgins are using that mode.
        :return: NA
        """
        self._vm_stat_callback = callback

    def get_vm_stat_callback(self):
        """
        This function returns state of vm_state

        :return: NA
        """
        return self._vm_stat_callback

    def tell_vm_stat(self, arg, val):
        """
        Pass along any tellVmStat() responses

        .. note:: Slightly modified from Synapse Uploader example
        """
        if self._vm_stat_callback is None:
            self.com.spy_upload_mgr.onTellVmStat(self.com.rpc_source_addr(), arg, val)
        else:
            self._vm_stat_callback(val)
            # LOGGER.debug("VmStat, Arg: " + str(arg) + ", Value: " + str(val))

    def su_recvd_reboot(self, *args):
        """
         Pass along any "reboot received" responses

        .. note:: Taken from Synapse Uploader example
        """
        self.com.spy_upload_mgr.on_recvd_reboot(self.com.rpc_source_addr())

    ## Base Node Reboot Methods ##
    def request_base_node_reboot(self):
        """
        Request base node reboot.
        We have to request base node reboot because we would like to reboot base node at
        the appropriate timing so sleepy mesh timing is not affected

        :return: NA
        """
        self._base_node_reboot_flag = True

    def check_base_node_reboot(self):
        """
        Check if we need to send reboot request to the base node.
        Send request if needed

        :return: True or False indicating if request has been sent
        """
        reboot_requested = False

        if self._base_node_reboot_flag:
            self._base_node_reboot_flag = False
            self.base_node_ucast('callback', 'brg__reboot', 'reboot')
            reboot_requested = True

        return reboot_requested

    ## Snap Shortcuts ##
    def add_callbacks(self, funcs):
        """
        Assigns callbacks to Snap Connect

        :param funcs: functions dictionary, where key is SnapPy function name as a string
            and a value of a key is a particular callback or a handler
        :return: NA

        .. note:: To my knowledge, it is possible to assign a function to a particular
            string (SnapPy function call) only once. It does not overwrite
            if a SnapPy function call already exists
        """
        for key, value in funcs.items():
            self.com.add_rpc_func(key, value)

    def base_node_ucast(self, *args):
        """
        Perform unicast to base node

        :param args: Arguments that should be send as part of the message
        :return: Returns message id

        .. note:: unicast performed as multicast with a TTL of 1,
            therefore message can reach only base node and network address is not needed
        """
        # LOGGER.debug("snap com ucast args = " + str(args))
        return self.com.mcast_rpc(1, 1, *args)

    def network_mcast(self, *args):
        """
        Send mcast to the network

        :param args: Arguments that should be send as part of the message
        :return: Returns message id
        """
        # LOGGER.debug("base mcast args = " + str(args))
        return self.base_node_ucast('mcastRpc', MCAST_GROUP, MCAST_TTL, *args)

    def mcast_rpc(self, *args):
        return self.com.mcast_rpc(MCAST_GROUP, MCAST_TTL, *args)

    def network_ucast(self, *args):
        """
        Send ucast to the network

        :param args: Arguments that should be send as part of the message
        :return: Returns message id
        """
        if len(args[0]) == NET_ADDR_STR_SIZE:
            # Convert net_addr
            args = list(args)
            args[0] = hex_to_bin(args[0])
            args = tuple(args)

        # LOGGER.debug("base ucast args = " + str(args))
        return self.base_node_ucast('rpc', *args)

    def poll_snap(self):
        """ Manual poll snap, shifts whole poll timing """
        self._poll_timer.stop()
        self._poll_timer.start()

    def set_polling_mode(self, polling_mode='sleep', polling_interval=None):
        """ Sets polling interval """
        if polling_interval is None:
            if polling_mode == 'awake':
                polling_interval = _SNAP_AWAKE_POLL
            else:
                polling_interval = _SNAP_SLEEP_POLL

        else:
            # Convert to ms
            polling_interval = int(polling_interval * 1000)

        self._poll_timer.stop()
        # LOGGER.debug('Polling set to ' + str(polling_interval) + ' ms')
        self._poll_timer.callback_time = polling_interval
        self._poll_timer.start()

    def _poll_snap(self):
        """ Internal Poll Snap """
        self.com.poll_internals()

    def schedule(self, delay, callable, *args, **kwargs):
        """ Schedule event """
        self._scheduler.schedule(delay, callable, *args, **kwargs)
