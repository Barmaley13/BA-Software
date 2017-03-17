"""
Users Web Handler with integrated Edit Methods
"""

### INCLUDES ###
import copy

from bottle import request

from gate.strings import VALIDATION_FAIL
from gate.conversions import internal_name

from gate.web.pages.handlers import WebHandlerOrderedDict


### CONSTANTS ###
## Strings ##
NO_USER = "No such user in the database!"


### CLASSES ###
class WebHandler(WebHandlerOrderedDict):
    def __init__(self, pages):
        super(WebHandler, self).__init__(pages, pages.users)

    def _remove(self, user_key):
        """ Removing user """
        # Last user that we are about to delete?
        # Last admin that we are about to delete?
        validate = not(len(self._object) <= 1) and self.admin_present(user_key, 'no_access', False)

        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if validate:
            # Log out current user (if needed)
            if self._object.current_user()['name'] == self._object[user_key]['name']:
                self._object.log_out()

            return_dict = super(WebHandler, self)._remove(user_key)

            self._object.save()
        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict

    def _update_user(self, user_key):
        """ Update/Create users """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        admin = self._object.check_access('admin')

        if not admin:
            user_key = internal_name(self._object.current_user()['name'])

        if admin or user_key in self._object.keys():
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
                validate &= not(self.name_taken(user_key, username))

                # Make sure both password fields match
                validate &= (password1 == password2)

            if admin:
                access = request.forms.total_access.encode('ascii', 'ignore')
                active = bool(request.forms.active)

                # Check if admin exists already
                validate &= self.admin_present(user_key, access, active)

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
                self._object.update_user(user_key, save_dict)

                if user_key in self._object.keys():
                    # Updating user properties
                    self._object[user_key].update(save_dict)

                    if username:
                        # Renaming user
                        new_user_key = internal_name(username)
                        if user_key != new_user_key:
                            default_dict = copy.deepcopy(self._object[user_key])
                            self._object.insert_before(user_key, (new_user_key, default_dict))
                            self._object[new_user_key].update(save_dict)
                            del self._object[user_key]

                            # Create new cookie
                            new_cookie = self._pages.get_cookie()
                            new_cookie['index'] = new_user_key
                            return_dict['new_cookie'] = new_cookie
                            return_dict['save_cookie'] = True

                elif username:
                    # Creating new user
                    new_user_key = internal_name(username)
                    # FYI: self._object[new_user_key] will provide default value (since it does not exist yet)
                    self._object[new_user_key] = copy.deepcopy(self._object[new_user_key])
                    self._object[new_user_key].update(save_dict)

                self._object.save()

            else:
                return_dict['kwargs']['alert'] = VALIDATION_FAIL
        else:
            return_dict['kwargs']['alert'] = NO_USER

        return return_dict

    def _toggle_user_bypass(self, user_key):
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

    def name_validation(self, address, prospective_name, **kwargs):
        """ Overloading validation for the users """
        json_dict = super(WebHandler, self).name_validation(address, prospective_name)
        json_dict['admin_present'] = int(self.admin_present(address, **kwargs))

        return json_dict

    def admin_present(self, current_user_key, access, active):
        """ Checks if admin is present in the system. Returns True or False """
        output = False

        for user_key, user in self._object.items():
            _access = self._object.check_access('admin', user=user)
            _active = user['active']
            if user_key == current_user_key:
                _access = bool(access == 'admin')
                _active = active

            if _access and _active:
                output = True
                break

        return output
