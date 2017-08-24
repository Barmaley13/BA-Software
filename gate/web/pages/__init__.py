"""
Web Pages Related Intricacies
"""

### INCLUDES ###
import os
import yaml
import logging

import bottle
from bottle import template, request

from gate.common import TPL_FOLDER

from .base import init_page
from .json_data import PagesJsonData


### CONSTANTS ###
## Strings ##
AJAX_ERROR = "AJAX ERROR: "
NO_FORM_NAMED1 = "Web form named "
NO_FORM_NAMED2 = " does not exist!"
WRONG_FORMAT = "Wrong Format!"
NO_FORM = "Request did not specify form!"
NO_AJAX_DATA = "No ajax data!"
POST_DENIED = "User does not have sufficient rights to process this request!"
NO_WEB_METHOD = "Request can not be processed!"

## Bottle Templates ##
_TEMPLATE_PATH = os.path.dirname(os.path.realpath(__file__))
bottle.TEMPLATE_PATH.append(_TEMPLATE_PATH)

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def _split_url(input_url):
    url_list = input_url.split('/')
    form_name = url_list.pop(-1)
    form_url = '/'.join(url_list)

    return form_url, form_name


### CLASSES ###
class WebPages(PagesJsonData):
    """ Pages Class """
    def __init__(self, **kwargs):
        super(WebPages, self).__init__(**kwargs)

        self._data_forms = {'live_data': self._forms[0], 'logs_data': self._forms[1]}

        ## Misc ##
        # TODO: Add function to return upload_type. Make this member private.
        # Note: This is used only by software.tpl at the moment
        self.upload_types = {
            self.template('nodes_subpage'): 'node',
            self.template('network_subpage'): 'base',
            self.template('system_home'): 'gate',
            self.template('logs_data'): 'log'
        }

        # Initialize group sub links
        self._data_page_refresh()

    ## Public Methods ##
    # Forms #
    def post_request(self, url):
        """ Process post request """
        ajax = None
        json_dict = {}
        kwargs = {}

        handler_tuple = self._parse('post_handler')
        if handler_tuple is not None:
            post_handler = handler_tuple[0]
            post_access = handler_tuple[1]

            action_method = request.forms.action_method.encode('ascii', 'ignore')
            # LOGGER.debug('action_method: ' + str(action_method))

            # FIXME: This should go away when we move cookie scheme to link addressing
            if action_method == 'load_base_page':
                post_access = 'read'

            if self.users.check_access(post_access):
                ajax = request.forms.ajax

                if action_method == 'login_user':
                    address = url
                else:
                    address = self.get_cookie()

                handler_dict = post_handler.handle(address)
                if handler_dict['save_cookie'] and 'new_cookie' in handler_dict:
                    new_cookie = handler_dict['new_cookie']
                    self.set_cookie(new_cookie)
                    json_dict['new_cookie'] = new_cookie

                    # LOGGER.debug('New Cookie: ' + str(new_cookie))

                if 'new_page' in handler_dict:
                    return handler_dict['new_page']
                else:
                    kwargs.update(handler_dict['kwargs'])
            else:
                kwargs.update({'alert': POST_DENIED})
        else:
            kwargs.update({'alert': NO_WEB_METHOD})

        if ajax:
            if 'alert' in kwargs:
                json_dict['alert'] = kwargs['alert']

            json_dict['software_overlay'] = template('software_overlay')

            return json_dict
        else:
            return template('main', kwargs)

    def get_form(self):
        """ Fetches requested form """
        json_dict = {}
        form_key = 'form'

        # Form Fetch #
        if request.query.data:
            data = yaml.safe_load(request.query.data)

            # LOGGER.debug("data = " + str(data))

            if 'url' in data:
                input_form_url, input_form_name = _split_url(data['url'])
                # LOGGER.debug("input_form_url: " + str(input_form_url))
                # LOGGER.debug("input_form_name: " + str(input_form_name))

                # Select page
                self.select_page(input_form_url)
                # Fetch proper(full) url
                _url = self.url()

                if 'cookies' in data:
                    # LOGGER.debug("New Cookie: " + str(data['cookies']))
                    self.users.update_current_user_cookies({_url: data['cookies']}, pre_format_cookies=True)
                    # LOGGER.debug('requested form = ' + str(_url) + '/' + str(input_form_name))

                # Kwargs
                kwargs = {'url': data['url']}
                if 'kwargs' in data:
                    kwargs.update(data['kwargs'])

                for form in self._forms:
                    # LOGGER.debug('form url: ' + str(form['template']))
                    form_template, form_name = _split_url(form['template'].replace(os.sep, '/'))
                    # TODO: Might wanna create separate pages for login/logout
                    # As of now there is a patch to fetch form on 'live', 'logs' pages
                    if input_form_name == form_name and \
                            (form_template in input_form_url or input_form_url in ('login', 'logout')):
                        for data_page in ('live_data', 'logs_data'):
                            if form == self._data_forms[data_page] and _url != self.url(data_page):
                                kwargs.update({'group_url': _url.split('/')[-1]})
                                break
                        tpl = self.__fetch_form_html(form, kwargs)
                        break
                else:
                    # Dynamic form creation
                    template_path = os.path.join(os.path.join(*_url.split('/')), input_form_name)
                    if os.path.isfile(os.path.join(TPL_FOLDER, template_path + '.tpl')):
                        new_form = {
                            'template': template_path,
                            'get_handler': self._parse('get_handler')
                        }

                        self._forms.append(new_form)

                        tpl = self.__fetch_form_html(new_form, kwargs)
                    else:
                        tpl = '<p>' + AJAX_ERROR + NO_FORM_NAMED1 + data['url'] + NO_FORM_NAMED2 + '</p>'

                # Post processing
                if input_form_name == 'table':
                    form_key = 'table'

                if type(tpl) in (str, unicode, dict):
                    if type(tpl) in (str, unicode):
                        json_dict[form_key] = tpl
                    elif type(tpl) is dict:
                        json_dict.update(tpl)

                    json_dict['software_overlay'] = template('software_overlay')
                    json_dict.update(self._json_for_ajax_update())

                    # Delete form when warning is prompted
                    if self.url('nodes_subpage') in self.url():
                        # TODO: detect what kind of form we are talking about
                        if not len(self.platforms.select_nodes('all')):
                            json_dict.update({'form': ''})

                else:
                    # LOGGER.debug("type(tpl) = " + str(type(tpl)))
                    json_dict[form_key] = '<p>' + AJAX_ERROR + WRONG_FORMAT + '</p>'
            else:
                json_dict[form_key] = '<p>' + AJAX_ERROR + NO_FORM + '</p>'
        else:
            json_dict[form_key] = '<p>' + AJAX_ERROR + NO_AJAX_DATA + '</p>'

        return json_dict

    # Websocket #
    def websocket_html(self):
        """ Fetches websocket related html/JavaScript (if enabled) """
        output = ''

        if self.users.check_access('user') and not self['login_page']['selected']:
            output += template('status')

            traps_ws_enable = self._parse('traps_ws_enable')
            if traps_ws_enable:
                output += template('traps')

        return output

    ## Class-Private Methods ##
    # Form Shortcuts Methods #
    def __fetch_form_html(self, form, kwargs):
        get_handler, get_access = form['get_handler']

        if get_access is not None and self.users.check_access(get_access):
            if get_handler is None:
                # LOGGER.debug("form tpl = " + form['template'])
                return template(form['template'], **kwargs)
            else:
                # LOGGER.debug("kwargs = " + str(kwargs))
                del kwargs['url']
                return get_handler(**kwargs)
        else:
            return "<p>AJAX ERROR: Access Denied!</p>"
