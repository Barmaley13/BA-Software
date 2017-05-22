"""
Some Main Functions
"""

### INCLUDES ###
import os
import bottle
import logging

from tornado import ioloop

from .common import CWD, TPL_FOLDER, OPTIONS_PARSER
from .system import SystemSettings
from .web import WebServer
from .web.socket import WebsocketManager
from .sleepy_mesh import SleepyMeshManager


### CONSTANTS ###
AES_RESET_DELAY = 3.0       # seconds


### MAIN FUNCTION ###
def main(system_options):
    """ Main function """
    # Make some variables accessible to html templates
    global manager, system_settings, pages, users, snmp_agents, snmp_commands, snmp_traps

    # Set current working directory
    os.chdir(CWD)
    # print('CWD: {}'.format(CWD))

    # Set default logging across all modules
    logging.basicConfig(level=logging.ERROR)

    # Set default bottle Template Path
    # del bottle.TEMPLATE_PATH[:]
    bottle.TEMPLATE_PATH.append(TPL_FOLDER)

    # Create and start Sleepy Mesh Manager (System Settings start modbus if it is enable)
    system_settings = SystemSettings(system_options)
    manager = SleepyMeshManager(
        system_settings=system_settings,
        websocket=WebsocketManager(),
        snmp_websocket=WebsocketManager()
    )
    manager.start()

    # Forward SNMP Agents/Commands/Traps to templates
    snmp_agents = manager.snmp_server.agents
    snmp_commands = manager.snmp_server.commands
    snmp_traps = manager.snmp_server.traps

    # Create Web Server
    # Web server is a loop, sleepy mesh manager scheduler is based on the same loop as well
    web_server = WebServer(manager)

    # Share some variables with html templates variables
    pages = web_server.pages
    users = web_server.pages.users

    # Start Web Server
    web_server.start()

    # If we are here it means that program has been terminated, kill modbus server
    manager.modbus_server.stop()
    manager.snmp_server.stop()


def reset_aes_settings(reset_complete_callback=None):
    """ Reset AES settings (if needed) """
    global manager

    # Set current working directory
    os.chdir(CWD)
    # print('CWD: {}'.format(CWD))

    # Set default logging across all modules
    logging.basicConfig(level=logging.ERROR)

    # Create System Options
    (system_options, args) = OPTIONS_PARSER.parse_args()
    # Disable modbus and snmp servers
    system_options.modbus_enable = False
    system_options.snmp_enable = False

    # Create and start Sleepy Mesh Manager
    system_settings = SystemSettings(system_options)
    manager = SleepyMeshManager(
        system_settings=system_settings,
        websocket=WebsocketManager(),
        snmp_websocket=WebsocketManager()
    )

    # Dynamically creating AES reset function so we can incorporate delay
    def _aes_reset():
        """ Nested AES Reset """
        # Dynamically creating reset complete callback
        def _reset_complete_callback():
            """ Nested Reset Complete Callback """
            # Stopping Scheduler
            manager.stop_scheduler()

            # Stopping Tornado Server
            ioloop.IOLoop.instance().stop()

            if reset_complete_callback is not None:
                reset_complete_callback()

        manager.reset_network(complete_callback=_reset_complete_callback)

    # Monkey Patching Scheduler
    old_start_scheduler = manager.init_scheduler

    def monkey_patched_init_scheduler():
        """ Monkey patching Init Scheduler to include AES Reset """
        old_start_scheduler()
        manager.bridge.schedule(AES_RESET_DELAY, _aes_reset)

    manager.init_scheduler = monkey_patched_init_scheduler

    # Delete all active nodes
    nodes = manager.platforms.select_nodes('active').values()
    for node in nodes:
        manager.platforms.delete_node(node)
        node.delete()

    # Starting Scheduler
    manager.start()

    # Starting Tornado
    ioloop.IOLoop.instance().start()
