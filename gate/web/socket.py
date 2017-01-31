"""
Websocket related intricacies
"""

### INCLUDES ###
import json
import logging

from tornado import websocket

from ..leds import off, green, red, yellow


### CONSTANTS ###
## Web Socket Message Types and Led Signals ##
# NOTE: Any additions will require status.tpl modification
# This list is mostly for reference purposes, error will be
# prompted if message is unknown
WEBSOCKET_LED_MAP = {
    'ws_default': yellow,
    'ws_awake': green,
    'ws_sleep': off,
    'ws_init': red,
    'ws_append': red,
    'ws_finish': off,
    'ws_reload': off
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
## Websocket ##
class WebsocketManager(object):
    """ Class managing websocket connections """
    def __init__(self):
        # Web Socket List
        self.ws_list = []
        # Buffer to store status messages during software update
        self._message_buffer = ''

    def send(self, message, message_type='ws_default', progress=None):
        """ Sends message via websocket. Keep buffer updated """
        # Sending String to web client via web sockets
        print message
        # Otherwise we get too many messages
        # if progress is None:
        #     print message

        if type(progress) in (int, float):
            progress = '{0:.2f}'.format(progress)
        
        # Long Polling
        # web.stdin.write(message + "\n")

        # Web Socket
        for socket in self.ws_list:
            if socket.ws_connection.stream.socket:
                socket.write_message(json.dumps({
                    'type': message_type,
                    'message': message,
                    'progress': progress
                }))

            else:
                LOGGER.warning("Web socket does not exist anymore!!!")
                self.ws_list.remove(socket)

        if message_type in WEBSOCKET_LED_MAP:
            # Signal led
            WEBSOCKET_LED_MAP[message_type]()
            
            # Manage websocket buffer
            if message_type in ('ws_init', 'ws_append'):
                if message_type == 'ws_append':
                    self._message_buffer += message
                else:
                    self._message_buffer = message

            elif message_type in ('ws_finish', ):
                self._message_buffer = ''

        else:
            LOGGER.error("Websocket message type of " + str(message_type) + " is invalid!")

        # LOGGER.debug('Message Buffer: ' + str(self._message_buffer))

    def buffer(self):
        """ Fetch content of the websocket buffer """
        return self._message_buffer

    def add_socket(self, socket):
        """ Adds socket to socket list """
        if socket not in self.ws_list:
            self.ws_list.append(socket)
            
    def remove_socket(self, socket):
        """ Remove socket from socket list """
        if socket in self.ws_list:
            self.ws_list.remove(socket)
        
    def close(self):
        """ Close Web Sockets. Currently not used """
        for socket in self.ws_list:
            socket.close()


## Tornado ##
class WebsocketHandler(websocket.WebSocketHandler):
    """ Custom Web Socket Handler """
    # noinspection PyMethodOverriding,PyAttributeOutsideInit
    def initialize(self, ws_manager):
        self.ws_manager = ws_manager

    def open(self):
        """ Executed at websocket open """
        LOGGER.debug('Online')
        self.ws_manager.add_socket(self)

    def on_message(self, message):
        """ Executed on websocket message """
        # self.write_message(message)
        LOGGER.debug('Message: ' + message)

    def on_close(self):
        """ Executed at websocket close """
        LOGGER.debug('Offline')
        self.ws_manager.remove_socket(self)
