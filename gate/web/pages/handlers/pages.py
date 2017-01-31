"""
Pages Web Handler with integrated Edit Methods
"""

### INCLUDES ###
from bottle import request

from gate.web.pages.handlers import WebHandlerBase


### CONSTANTS ###
## Strings ##
CREDENTIALS_FAIL = "Wrong Username or Password! Please try again!"
CREDENTIALS_MISSING = "Username and/or password are/is missing!"


### CLASSES ###
class WebHandler(WebHandlerBase):
    def __init__(self, pages):
        super(WebHandler, self).__init__(pages, pages)

    def handle(self, cookie):
        """ Overwriting default handle method """
        action_method = request.forms.action_method.encode('ascii', 'ignore')
        if hasattr(self, '_' + action_method):
            return super(WebHandler, self).handle(cookie)
        else:
            return self._pages.handlers['system'].handle(cookie)

    def _login_user(self, url):
        return_dict = {'kwargs': {}, 'save_cookie': False}

        if request.forms.username and request.forms.password:
            username = request.forms.username.encode('ascii', 'ignore')
            password = request.forms.password.encode('ascii', 'ignore')

            # Set cookies and access
            if self._pages.users.log_in(username, password):
                self._pages.select_page(url)
                self._pages.reset_cookies()

            else:
                return_dict['kwargs']['alert'] = CREDENTIALS_FAIL
        else:
            return_dict['kwargs']['alert'] = CREDENTIALS_MISSING

        return return_dict

    def _save_software(self, cookie):
        """ Just a buffer """
        nodes = self._manager.platforms.select_nodes('active').values()
        return self._manager.uploader.init_upload('gate', nodes)
