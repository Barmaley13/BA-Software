"""
HTTP Web Server Engine with Custom Tornado Adapter that includes websocket support
"""

### INCLUDES ###
import logging

from tornado import web, wsgi, httpserver, ioloop
import bottle

from .application import WebApplication
from .socket import WebsocketHandler


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
## Bottle Adapter ##
class CustomTornado(bottle.ServerAdapter):
    """ Custom Tornado Web Server Adapter. Includes Web Socket Support. """

    def __init__(self, host='127.0.0.1', port=8080, **options):
        ## Generic Variables ##
        super(CustomTornado, self).__init__(host=host, port=port, **options)
        ## Extras ##
        self.handlers = []
        # Web Socket Handlers #
        self.handlers.append((r'/status', WebsocketHandler, {'ws_manager': self.options['ws_manager0']}))
        self.handlers.append((r'/traps', WebsocketHandler, {'ws_manager': self.options['ws_manager1']}))
        # HTML Handler #
        self.handlers.append((r".*", web.FallbackHandler, {'fallback': wsgi.WSGIContainer(self.options['web_app'])}))
        # Server Instances #
        self.tornado_app = web.Application(self.handlers)
        self.server = httpserver.HTTPServer(self.tornado_app)
        self.ioloop = ioloop.IOLoop.instance()
        # self.ioloop.set_blocking_log_threshold(0.25)

    def run(self, handler=None):  # pragma: no cover
        """ Run custom server method """
        self.server.listen(self.port)
        self.ioloop.start()

    def stop(self):
        """ Stop custom server method """
        self.server.stop()
        self.ioloop.stop()


class WebServer(WebApplication):
    """ Web Server containing all web related instances """
    def __init__(self, *args):
        super(WebServer, self).__init__(*args)

    def start(self):
        """ Start Web Server """

        ## Start Web Server ##
        # debug == False => Restart server for newer templates
        # debug == True => Templates are reloaded automatically
        self._app.run(
            server=CustomTornado,
            host='0.0.0.0',
            port=80,
            quiet=True,
            debug=True,
            # Those are passed as options but they are needed for our custom server
            web_app=self._app,
            ws_manager0=self._websocket,
            ws_manager1=self._snmp_websocket,

        )
