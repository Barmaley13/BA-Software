"""
Web Server Application
"""

### INCLUDES ###
import os
import logging

from bottle import Bottle, template, static_file

from gate.common import MWD

from pages import WebPages


### CONSTANTS ###
## Web Server Static Files ##
STATIC_FILES = ('favicon.ico', 'js', 'img', 'style', 'audio')

## Dynamic Routing Defaults ##
# Note: Make sure to change dynamic_route and dynamic_post accordingly if changed
DYNAMIC_ROUTES_DEFAULTS = [
    '/',
    '/<url0>',
    '/<url0>/',
    '/<url0>/<url1>',
    '/<url0>/<url1>/',
    '/<url0>/<url1>/<url2>',
    '/<url0>/<url1>/<url2>/',
    '/<url0>/<url1>/<url2>/<url3>',
    '/<url0>/<url1>/<url2>/<url3>/'
]

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def compose_url(url_list):
    """ Composes url in to a string """
    output = ''

    for url_index, url in enumerate(url_list):
        if url is not None:
            if url_index != 0:
                output += '/'

            # Note: We are not allowed to have spaces in any html page names!
            if ' ' in url:
                url = url.replace(' ', '+')

            output += url

        else:
            break

    return output


### CLASSES ###
class WebApplication(object):
    """
    Used this answer to build this class
    http://stackoverflow.com/questions/8725605/bottle-framework-and-oop-using-method-instead-of-function
    """

    def __init__(self, manager):
        self._app = Bottle()
        self._websocket = manager.websocket
        self._snmp_websocket = manager.snmp_websocket
        self.pages = WebPages(manager=manager)

        ## Register Methods with Bottle App ##
        # Route and Post Methods #
        # IMPORTANT!: Route and Post has to match
        for route in DYNAMIC_ROUTES_DEFAULTS:
            self._app.route(route)(self.dynamic_route)
            self._app.post(route)(self.dynamic_post)

        # Missing Page Method #
        self._app.error(404)(self.page_not_found)

        # Get Method #
        self._app.get('/ajax')(self.get_form)

    ## Route Method ##
    def dynamic_route(self, url0=None, url1=None, url2=None, url3=None, url4=None):
        """ Dynamic routing for all html requests """
        url = compose_url([url0, url1, url2, url3, url4])
        # LOGGER.debug("url 0 = " + str(url))

        if url0 in STATIC_FILES:
            # print 'url = ', url
            url_list = url.split('/')
            file_name = url_list.pop(-1)
            # LOGGER.debug('file_name = ' + file_name)
            file_path = os.path.join(MWD, *url_list)
            # LOGGER.debug('file_path = ' + file_path)
            return static_file(file_name, root=file_path)

        elif url0 == 'logout':
            self.pages.users.log_out()
            self.pages.select_page(url)
        else:
            self.pages.users.load_user()
            self.pages.select_page(url)
        return template('main')

    ## Post Method ##
    def dynamic_post(self, url0=None, url1=None, url2=None, url3=None):
        """ Responses to post method """
        url = compose_url([url0, url1, url2, url3])

        self.pages.users.load_user()
        self.pages.select_page(url)

        return self.pages.post_request(url)

    ## Get Method (aka AJAX) ##
    def get_form(self):
        """ Responses to get method """
        self.pages.users.load_user()

        return self.pages.get_form()

    ## Missing Page Method ##
    def page_not_found(self, error_code):
        """ Page not found response """
        LOGGER.warning('Page not found! Error code: ' + str(error_code))
        return template('main')


## STATUS (via AJAX LONG POLLING) ##
# NOT USED CURRENTLY!
# @APP.get('/status')
# def status():
#     flush = request.query.flush
#     if flush == 'True':
#         # This stdin flush works only on unix like systems
#         sys.stdout.flush()
#         while len(select.select([sys.stdin.fileno()], [], [], 0.0)[0]) > 0:
#             os.read(sys.stdin.fileno(), 4096)
#     data = raw_input()
#     return data
#     #time.sleep(1)
#     #return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
