"""
SNMP Process Queue and SNMP Process
"""

### INCLUDES ###
import os
from multiprocessing import Process
import logging

from py_knife import pickle

from gate.common import DATABASE_FOLDER, SIDE_PROCESS_NICENESS
from gate.database import DatabaseList

from agents import SNMPAgent


### CONSTANTS ###
SNMP_QUEUE_FILE = os.path.join('snmp', 'queue.db')
SNMP_QUEUE_PATH = os.path.join(DATABASE_FOLDER, SNMP_QUEUE_FILE)

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class SNMPProcess(Process):
    def __init__(self):
        super(SNMPProcess, self).__init__()

    def run(self):
        """ Executes SNMP commands from the queue, FIFO style """
        process_niceness = os.nice(SIDE_PROCESS_NICENESS)
        LOGGER.debug('snmp command execute niceness = ' + str(process_niceness))

        process_queue = pickle.unpickle_file(SNMP_QUEUE_PATH)
        if process_queue is not False:
            # LOGGER.debug("Process - Load: " + str(len(process_queue)))
            while len(process_queue):
                snmp_agent_kwargs = process_queue[0]['snmp_agent_kwargs']
                snmp_command = process_queue[0]['snmp_command']
                snmp_agent = SNMPAgent(**snmp_agent_kwargs)
                snmp_agent.execute(snmp_command)
                # LOGGER.debug("Process - Send: " + str(snmp_command))

                process_queue = pickle.unpickle_file(SNMP_QUEUE_PATH)
                if process_queue is False:
                    process_queue = list()

                # LOGGER.debug("Process - Load: " + str(len(process_queue)))

                # Remove this process from process queue
                if len(process_queue):
                    del process_queue[0]
                    # LOGGER.debug("Process - Remove: " + str(len(process_queue)))

                    pickle.pickle_file(SNMP_QUEUE_PATH, process_queue)
                    # LOGGER.debug("Process - Save: " + str(len(process_queue)))


class SNMPQueue(DatabaseList):
    """ Queue Class managing the processes (FIFO Style) """
    def __init__(self):
        super(SNMPQueue, self).__init__(
            db_file=SNMP_QUEUE_FILE
        )
        self.snmp_process = None

    def add(self, snmp_agent, snmp_command):
        """ Adds process to the queue """
        # Add process to the queue
        snmp_agent_kwargs = dict(snmp_agent.items())
        process_kwargs = {
            'snmp_agent_kwargs': snmp_agent_kwargs,
            'snmp_command': snmp_command
        }

        self.load()
        # LOGGER.debug("Queue - Load: " + str(len(self)))

        self.append(process_kwargs)
        # LOGGER.debug("Queue - Add: " + str(snmp_command))
        self.save()
        # LOGGER.debug("Queue - Save: " + str(len(self)))

        # Start process if needed
        if self.snmp_process is None or not self.snmp_process.is_alive():
            self.snmp_process = SNMPProcess()
            self.snmp_process.start()
