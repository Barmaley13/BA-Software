"""
Modbus Related Intricacies 
"""

### INCLUDES ###
import os
import signal
import struct
import logging
from multiprocessing import Process

# Sync Server Includes #
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.server.sync import ModbusTcpServer, ModbusConnectedRequestHandler

# Common Includes #
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.pdu import ModbusExceptions

from py_knife.pickle import unpickle_file

from .common import DATABASE_FOLDER
from .conversions import bin_to_int
from .database import DatabaseDict


### CONSTANTS ###
MODBUS_ADDRESS_RANGE = 9999

## Modbus Register Types ##
MODBUS_COILS = 1
MODBUS_DISCRETES = 2
MODBUS_HOLDING_REGISTERS = 3
MODBUS_INPUT_REGISTERS = 4
# Modbus Data #
MODBUS_DEFAULTS = {
    'modbus_data': {
        MODBUS_COILS: {},
        MODBUS_DISCRETES: {},
        MODBUS_HOLDING_REGISTERS: {},
        MODBUS_INPUT_REGISTERS: {}
    }
}
## Modbus Settings ##
MODBUS_REG_SELECT = MODBUS_HOLDING_REGISTERS
MODBUS_REG_NUM = 64

# Does not work properly in False Mode
MODBUS_FILL_EMPTY_DATA = True
# Notes on MODBUS_FILL_EMPTY_DATA
# Set true and modbus interface will return 0x00 for empty values
# Set false and modbus interface will return an invalid address exception

## Misc Constants ##
_ENDIAN_CHAR = ['<', '>']        # little_endian, big_endian

## Modbus File Name ##
MODBUS_FILE = 'modbus.db'
MODBUS_PATH = os.path.join(DATABASE_FOLDER, MODBUS_FILE)

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class CustomModbusHandler(ModbusConnectedRequestHandler):
    """ Hacked modbus handler """

    def _load_data(self):
        """ Function to update context that was set by sleepy mesh """
        modbus_database = unpickle_file(MODBUS_PATH)
        if modbus_database is not False:
            if 'modbus_data' in modbus_database:
                modbus_raw_data = modbus_database['modbus_data']
                # LOGGER.debug("modbus_raw_data = " + str(modbus_raw_data))

                # Reset all values to default
                self.server.context[0].reset()

                for field in modbus_raw_data:
                    if modbus_raw_data[field]:
                        if MODBUS_FILL_EMPTY_DATA:
                            for modbus_address, modbus_data in modbus_raw_data[field].items():
                                # LOGGER.debug('modbus_data[' + str(field) + '][' + str(modbus_address) + '] = '
                                #              + str(modbus_data))

                                self.server.context[0].setValues(field, modbus_address, [modbus_data])

                                # # Debugging - displaying provided data
                                # LOGGER.debug('modbus_data[' + str(field) + '][' + str(modbus_address) + ']')
                                # LOGGER.debug('provided data = ' + str(modbus_data))
                                #
                                # # Debugging - displaying internal server data
                                # read_data = self.server.context[0].getValues(field, modbus_address)
                                # LOGGER.debug('read data = ' + str(read_data))
                        else:
                            # LOGGER.debug('modbus_data[' + str(field) + '] = ' + str(modbus_raw_data[field]))

                            self.server.context[0].setValues(field, 0, modbus_raw_data[field])

                            # # Debugging - displaying provided data
                            # LOGGER.debug('modbus_data[' + str(field) + ']')
                            # LOGGER.debug('provided data = ' + str(modbus_raw_data[field]))
                            #
                            # # Debugging - displaying internal server data
                            # read_data = self.server.context[0].getValues(field, 0, len(modbus_raw_data))
                            # LOGGER.debug('read data = ' + str(read_data))

            else:
                LOGGER.error("Could not open modbus.json file successfully!")
        else:
            LOGGER.error("Could not open modbus.json file successfully!")

    def execute(self, request):
        """
         The callback to call with the resulting message

         .. warning:: DO NOT CHANGE! VERY SENSITIVE!
         """
        ## Custom ##
        self._load_data()

        ## Generic ##
        try:
            context = self.server.context[request.unit_id]
            response = request.execute(context)
        except Exception, ex:
            LOGGER.debug("Datastore unable to fulfill request: %s" % ex)
            response = request.doException(ModbusExceptions.SlaveFailure)
        response.transaction_id = request.transaction_id
        response.unit_id = request.unit_id
        self.send(response)


class ModbusProcess(Process):
    def __init__(self, system_settings):
        """
        Modified StartTcpServer from pymodbus.server.sync

        .. warning:: DO NOT CHANGE START TCP SERVER SECTION! VERY SENSITIVE!
        """
        identity = ModbusDeviceIdentification()
        identity.VendorName = system_settings['company']
        identity.ProductCode = system_settings['product']
        identity.VendorUrl = system_settings['url']
        identity.ProductName = system_settings['product']
        identity.ModelName = system_settings['version']
        identity.MajorMinorRevision = system_settings['version']

        framer = ModbusSocketFramer
        if MODBUS_FILL_EMPTY_DATA:
            slave = ModbusSlaveContext()
        else:
            # TODO: Complete this feature! Does not work properly at the moment!
            empty_block = ModbusSparseDataBlock({0x00: 0x00})
            slave = ModbusSlaveContext(di=empty_block, co=empty_block, hr=empty_block, ir=empty_block)

        # LOGGER.debug("slave.store = " + str(slave.store))
        context = ModbusServerContext(slaves=slave, single=True)
        self.server = ModbusTcpServer(context, framer)
        self.server.RequestHandlerClass = CustomModbusHandler
        super(ModbusProcess, self).__init__(target=self.server.serve_forever)


class ModbusServer(DatabaseDict):
    """ Modbus Interface. Used by sleepy_mesh and web """
    def __init__(self):
        self.address_counter = 0

        super(ModbusServer, self).__init__(
            db_file=MODBUS_FILE,
            defaults=MODBUS_DEFAULTS
        )

        self._running = False
        self._server_process = None

    ## System Methods ##
    def start(self, system_settings):
        """ Starts modbus server as a separate process """
        if not self._running:
            self._running = True
            self._server_process = ModbusProcess(system_settings)
            self._server_process.start()

    def stop(self):
        """ Stops modbus server """
        if self._running:
            # LOGGER.debug('Here1!')
            server_pid = self._server_process.pid
            os.kill(server_pid, signal.SIGTERM)
            # LOGGER.debug('Here2!')
            self._running = False

    ## Sleepy Mesh Methods ##
    def _clear_data(self):
        """ Clears modbus data """
        if self._running:
            for key in self['modbus_data']:
                self['modbus_data'][key].clear()

    def _write_data(self, node, modbus_address, modbus_data):
        """ Appends modbus data """
        if self._running:
            if modbus_address <= MODBUS_ADDRESS_RANGE:
                if node['modbus_addr'] <= modbus_address < (node['modbus_addr'] + MODBUS_REG_NUM):
                    # Binary String (2 char long) #
                    if type(modbus_data) is str and len(modbus_data) == 2:
                        modbus_data = bin_to_int(modbus_data)
                    # Integer #
                    if type(modbus_data) is int:
                        modbus_data &= 0xFFFF
                        self['modbus_data'][MODBUS_REG_SELECT].update({modbus_address: modbus_data})
                    else:
                        LOGGER.error("Wrong data format!")
                else:
                    LOGGER.error("Node register space overflow error!")
            else:
                LOGGER.error("Address space overflow error!")

        return modbus_address + 1

    def _extract_data(self, node, modbus_settings):
        """ Extracts modbus data from a node """
        # LOGGER.debug("Node: " + node['net_addr'])

        # Addressing
        base_address = node['modbus_addr']
        if base_address is not None:
            node_address1 = base_address + 0
            node_address2 = base_address + 1
            status_address1 = base_address + 2
            status_address2 = base_address + 3
            data_address = base_address + 4

            # Append modbus data with network address
            net_addr = struct.pack('!I', (int(node['net_addr'], 16) & 0xFFFFFFFF))
            self._write_data(node, node_address1, net_addr[:2])
            self._write_data(node, node_address2, net_addr[2:])

            # Append modbus data with enabled data
            display_headers = node.read_headers('display').values()
            for header in display_headers:
                modbus_units = header.modbus_units()
                current_value = modbus_units.get_float(node)
                # LOGGER.debug('header = ' + header['internal_name'] + ', units = ' + modbus_units['internal_name'])
                # LOGGER.debug('address = ' + str(data_address) + ', value = ' + str(current_value))

                if current_value is None:
                    current_value = 0

                endian_char = _ENDIAN_CHAR[int(modbus_settings['modbus_byte_order'])]
                mdb_value = struct.pack(endian_char + 'f', float(current_value))
                if not modbus_settings['modbus_register_order']:
                    data_address = self._write_data(node, data_address, mdb_value[:2])
                    data_address = self._write_data(node, data_address, mdb_value[2:])
                else:
                    data_address = self._write_data(node, data_address, mdb_value[2:])
                    data_address = self._write_data(node, data_address, mdb_value[:2])

            # Append modbus data with status register
            modbus_status = node.error.modbus_status()
            self._write_data(node, status_address1, modbus_status[0])
            self._write_data(node, status_address2, modbus_status[1])

    def extract_data(self, nodes, modbus_settings):
        """ Takes data from nodes, formats it and writes it to modbus output """
        if self._running:
            self._clear_data()

            for node in nodes.values():
                self._extract_data(node, modbus_settings)

            # LOGGER.debug('write data = ' + str(self['modbus_data']))
