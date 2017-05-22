"""
Update Interface
"""

### INCLUDES ###
# from multiprocessing import Process
from threading import Thread
import logging

from gate.database import DatabaseList


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class WorkerThread(Thread):
    """ Worker based on Thread class """
    def __init__(self):
        super(WorkerThread, self).__init__()
        self._running = False

    def set_running(self, running_state):
        self._running = running_state

    def get_running(self):
        return self._running

    def stop(self):
        if self.get_running():
            self.set_running(False)
            self.join()


class UpdateInterfaces(DatabaseList):
    def __init__(self, manager):
        super(UpdateInterfaces, self).__init__()
        self.websocket = manager.websocket

    def update_in_progress(self, *match_update_types):
        """ Tells web interface if update is in progress as well as type of update """
        # print('match_update_types: {}'.format(match_update_types))

        if len(match_update_types) == 0:
            match_update_types = None

        output = None
        # LOGGER.debug('Update Interfaces: ' + str(len(self)))
        for update_interface in iter(self):
            update_type = update_interface.update_type(match_update_types)
            if update_type is not None:
                output = update_type
                break

        # print('update_in_progress: {}'.format(output))

        return output

    def create(self, *args, **kwargs):
        """ Creates new update interface """
        self.append(UpdateInterface(self.websocket, *args, **kwargs))
        # LOGGER.debug('Creating Update Interface: ' + str(self[-1]))
        return self[-1]


class UpdateInterface(object):
    def __init__(self, websocket, update_types):
        self._websocket = websocket
        self._update_types = update_types

        # Update Engine #
        self._update_type = None

    def start_update(self, update_type):
        """
        Triggers update that will communicate to web interface to display
        software/network update window
        """
        LOGGER.debug("Starting update: " + str(update_type))

        if self._update_type is None:
            if update_type in self._update_types:
                self._update_type = update_type

            else:
                LOGGER.error("Provided update type: " + str(update_type) + " is invalid!")
        else:
            LOGGER.error("Can not start " + str(update_type) + " update! Update is in progress already!")

    def update_type(self, match_update_type=None):
        """
        Tells web interface if update is in progress
        as well as type of update
        """
        output = None

        # if self._update_type is not None:
        #     LOGGER.debug("self._update_type: " + str(self._update_type))
        #     LOGGER.debug("match_update_type update: " + str(match_update_type))

        found_match = bool(match_update_type is None)
        found_match |= bool(self._update_type == match_update_type)
        found_match |= bool(type(match_update_type) in (list, tuple) and self._update_type in match_update_type)

        if found_match:
            output = self._update_type

        return output

    def finish_update(self, finish_message=None):
        """ Finishes update by setting appropriate flag """
        LOGGER.debug("Finishing update: " + finish_message)

        # if self['_update_type'] is None:
        #     LOGGER.error("Can not finish update! No update that is in progress!")

        self._update_type = None

        if finish_message is not None:
            self._websocket.send(finish_message, 'ws_finish', 100.0)
