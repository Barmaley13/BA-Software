"""
SNMP Trap Server
References:
http://pysnmp.sourceforge.net/examples/current/v3arch/manager/ntfrcv/v2c-multiple-interfaces.html
"""

### INCLUDES ###
import os
# import signal
import logging
# from multiprocessing import Process
from threading import Thread

from pysnmp.entity import engine, config
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv

from py_knife import pickle

from gate.common import DATABASE_FOLDER
from gate.conversions import get_net_addresses
from gate.database import DatabaseList

from queue import SNMPQueue
from agents import SNMPAgents
from commands import SNMPCommands
from traps import SNMPTraps


### CONSTANTS ###
TRAPS_FILE = os.path.join('snmp', '_traps.db')
TRAPS_PATH = os.path.join(DATABASE_FOLDER, TRAPS_FILE)

## SNMP Server Constants ##
SNMP_TRAP_PORT = 162
SNMP_TRAP_COMMUNITY = 'public'

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
# class SNMPTrapServerProcess(Process):
class SNMPTrapServerProcess(Thread):
    """ Actual Trap Server Process """
    def __init__(self, snmp_websocket):
        super(SNMPTrapServerProcess, self).__init__()
        self._snmp_websocket = snmp_websocket
        self.snmp_engine = None

    def callback_function(self, _snmp_engine, state_reference, context_engine_id, context_name, var_binds, cb_ctx):
        """ Incoming Trap Parser """
        trap = {'ip_address': '', 'oid': '', 'value': ''}

        # Retrieve trap data
        transport_domain, transport_address = _snmp_engine.msgAndPduDsp.getTransportInfo(state_reference)
        trap['ip_address'] = str(transport_address[0])

        del var_binds[:-1]
        for oid, val in var_binds:
            trap['oid'] = str(oid.prettyPrint())
            trap['value'] = str(val.prettyPrint())

        # Append trap data to traps file
        traps = pickle.unpickle_file(TRAPS_PATH)

        if traps is False:
            traps = list()

        traps.append(trap)

        pickle.pickle_file(TRAPS_PATH, traps)

        # Send message to traps websocket
        trap_info_message = ''
        trap_info_message += 'SNMP Agent IP: ' + trap['ip_address']
        trap_info_message += ' Trap OID: ' + trap['oid']
        trap_info_message += ' Trap Value: ' + trap['value']

        self._snmp_websocket.send(trap_info_message)

    def run(self):
        """ Main Transport Dispatcher Loop """
        # Create SNMP engine with auto generated engineID and pre-bound
        # to socket transport dispatcher
        self.snmp_engine = engine.SnmpEngine()

        # Transport setup
        ip_address, net_mask = get_net_addresses()
        # UDP over IPv4, first listening interface/port
        config.addSocketTransport(
            self.snmp_engine,
            udp.domainName + (1,),
            udp.UdpTransport().openServerMode((ip_address, SNMP_TRAP_PORT))
        )

        # SNMPv1/2c setup
        # SecurityName <-> CommunityName mapping
        config.addV1System(self.snmp_engine, 'my-area', SNMP_TRAP_COMMUNITY)

        # Register SNMP Application at the SNMP engine
        ntfrcv.NotificationReceiver(self.snmp_engine, self.callback_function)

        # this job would never finish
        self.snmp_engine.transportDispatcher.jobStarted(1)

        # Run I/O dispatcher which would receive queries and send confirmations
        try:
            self.snmp_engine.transportDispatcher.runDispatcher()
        except:
            self.snmp_engine.transportDispatcher.closeDispatcher()
            raise


class SNMPTrapServer(DatabaseList):
    """ Wrapper that provides means to start and stop server """
    def __init__(self, manager):
        super(SNMPTrapServer, self).__init__(
            db_file=TRAPS_FILE
        )

        self.queue = SNMPQueue()
        self.agents = SNMPAgents()
        self.commands = SNMPCommands()
        self.traps = SNMPTraps()

        self._manager = manager
        self._snmp_websocket = manager.snmp_websocket

        self._running = False
        self._server_process = None

    ## System Methods ##
    def start(self):
        """ Starts snmp trap server as a separate process """
        if not self._running:
            self._running = True
            self._server_process = SNMPTrapServerProcess(self._snmp_websocket)
            self._server_process.start()

    def stop(self):
        """ Stops snmp trap server """
        if self._running:
            # # LOGGER.debug('Here1!')
            # server_pid = self._server_process.pid
            # os.kill(server_pid, signal.SIGTERM)
            # # LOGGER.debug('Here2!')

            self._server_process.snmp_engine.transportDispatcher.jobFinished(1)
            self._running = False

    def restart(self):
        """ Restarts snmp trap server """
        self.stop()
        self.start()

    # TODO: Make immediate! (Might fuck things up!)
    def parse_traps(self, nodes):
        """ Parses traps, executes node acks if matched """
        if self._running:
            self.load()

            # Match loaded traps and existing traps
            for _snmp_trap in iter(self):
                # print "_snmp_trap: ", str(_snmp_trap)
                for snmp_agent_key, snmp_agent in self.agents.items():
                    if snmp_agent['ip_address'] == _snmp_trap['ip_address']:
                        for snmp_trap_key, snmp_trap in self.traps.items():
                            # print "snmp_trap: ", str(snmp_trap)
                            if snmp_trap['oid'] == _snmp_trap['oid']:
                                if snmp_trap['value'] == _snmp_trap['value']:

                                    # Match node snmp traps with triggered traps
                                    for node in nodes.values():
                                        node.error.check_snmp_trap_ack(snmp_agent_key, snmp_trap_key)

                                    break

                        else:
                            continue

                        break

            # Clear trap list
            del self[:]

    def send_snmp(self, snmp_agent_key, snmp_command_key):
        """ Sends Set(or Clear) SNMP Command """
        snmp_agent = None
        snmp_command = None

        if snmp_agent_key in self.agents.keys():
            snmp_agent = self.agents[snmp_agent_key]
        if snmp_command_key in self.commands.keys():
            snmp_command = self.commands[snmp_command_key]

        self.queue.add(snmp_agent, snmp_command)

    # TODO: Get rid of manager here!!!
    def clear_snmp(self, snmp_agent, snmp_command):
        """ Clears SNMP Command """
        send_command = False

        nodes = self._manager.platforms.select_nodes('active')
        for node in nodes.values():
            send_command = node.error.check_snmp_clear_ack(snmp_agent, snmp_command)

            if not send_command:
                break

        if send_command:
            LOGGER.debug("Sending Clear SNMP Command")
            self.send_snmp(snmp_agent, snmp_command)
