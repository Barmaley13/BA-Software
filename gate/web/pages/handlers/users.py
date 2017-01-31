"""
Users Web Handler with integrated Edit Methods
"""

### INCLUDES ###
from bottle import request

from gate.strings import VALIDATION_FAIL

from gate.web.pages.handlers import WebHandlerList


### CONSTANTS ###
## Strings ##
NO_USER = "No such user in the database!"


### CLASSES ###
class WebHandler(WebHandlerList):
    def __init__(self, pages):
        super(WebHandler, self).__init__(pages, pages.users)

    def _remove(self, index):
        """ Removing user """
        # Last user that we are about to delete?
        # Last admin that we are about to delete?
        validate = not(len(self._object) <= 1) and self._object.admin_present(index, 'no_access', False)

        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if validate:
            # Log out current user (if needed)
            if self._object.current_user()['name'] == self._object[index]['name']:
                self._object.log_out()

            return_dict = super(WebHandler, self)._remove(index)

            self._object.save()
        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict

    def _update_user(self, index):
        """ Update/Create users """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        admin = self._object.check_access('admin')
        if admin or index < len(self._object):
            validate = True
            access = 'no_access'
            active = False

            # Get data from forms
            username = request.forms.username
            password1 = request.forms.password1
            password2 = request.forms.password2

            if username:
                username = username.encode('ascii', 'ignore')
                password1 = password1.encode('ascii', 'ignore')
                password2 = password2.encode('ascii', 'ignore')

                # Validate data
                validate_list = [username]
                # Make sure following values are not blanks
                for value in validate_list:
                    validate &= (len(value) > 0)

                # Check if username is already in use
                validate &= not(self._object.user_name_taken(index, username))

                # Make sure both password fields match
                validate &= (password1 == password2)

            if admin:
                access = request.forms.total_access.encode('ascii', 'ignore')
                active = bool(request.forms.active)

                # Check if admin exists already
                validate &= self._object.admin_present(index, access, active)

            if validate:
                # Create save dictionary
                save_dict = dict()

                if username:
                    save_dict = {'name': username}
                    if len(password1) > 0:
                        save_dict.update({'password': password1})

                if admin:
                    save_dict.update({'access': access, 'active': active})

                # Load local buffers with save dictionary
                self._object.update_user(index, save_dict)

                self._object.save()
            else:
                return_dict['kwargs']['alert'] = VALIDATION_FAIL
        else:
            return_dict['kwargs']['alert'] = NO_USER

        return return_dict

    def _toggle_user_bypass(self, index):
        """ Toggles User System Enable """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        admin = self._object.check_access('admin')
        if admin:
            # Create save dictionary
            save_dict = dict()
            save_dict['user_bypass'] = not self._manager.system_settings['user_bypass']
            self._manager.system_settings.update(save_dict)
            self._manager.system_settings.save()

        return return_dict
