"""
Users Related Intricacies
"""

### INCLUDES ###
import copy
import logging

from bottle import response, request

from py_knife.ordered_dict import OrderedDict

from ..database import DatabaseOrderedDict
from ..conversions import internal_name


### CONSTANTS ###
## Access Constants ##
ACCESS = {
    'no_access': 0,
    'user': 10,
    'read': 20,
    'write': 30,
    'admin': 40
}

## Default Users ##
# Note: name and password will be overwritten by system settings (refer to system.py)
DEFAULT_USER = {
    'name': 'admin',
    'password': 'admin',
    'access': 'admin',
    'active': True,
    'cookies': {}
}
    
NEW_USER_DEFAULTS = {
    'name': '',
    'password': '',
    'access': 'user',
    'active': True,
    'cookies': {}
}

GUEST_USER = {
    'name': 'Guest',
    'password': '',
    'access': 'no_access',
    'active': False,
    'cookies': {}
}

## Strings ##
USER_VALIDATION = '*User'
NAME_FREE = ' name is available'
NAME_EMPTY = ' name can not be empty!'
NAME_TAKEN = ' name is taken already!'

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###    
def _format_cookies(target, integer_check=True):
    """ Formats cookie from user to a safe one """
    target_keys = []
    if type(target) is dict:
        target_keys = target.keys()
    elif type(target) is list:
        target_keys = range(len(target))
    
    for key in target_keys:
        # Convert key if needed
        if type(target) is dict and type(key) is unicode:
            old_key = copy.deepcopy(key)
            key = key.encode('ascii', 'ignore')
            target[key] = target.pop(old_key)
        
        if type(target[key]) is dict or type(target[key]) is list:
            integer_check = not bool(key in ('nodes', ))
            _format_cookies(target[key], integer_check=integer_check)
        elif target[key] is not None:
            # LOGGER.debug("key = " + str(key))
            # LOGGER.debug("target[key] = " + str(target[key]))
            # LOGGER.debug("type(target[key]) = " + str(type(target[key])))
            if type(target[key]) is unicode:
                target[key] = target[key].encode('ascii', 'ignore')

                # TODO: This is very bad! Eliminate this shit!
                if integer_check and key != 'export_net_addr' and target[key].split('.')[0].isdigit():
                    target[key] = int(target[key])
    

### CLASSES ###
class Users(DatabaseOrderedDict):
    """ System related class """
    def __init__(self, callbacks, system):
        self._callbacks = callbacks
        self._system_settings = system

        self.validation_string = USER_VALIDATION
        self.new_defaults = NEW_USER_DEFAULTS

        # User Related #
        default_user = copy.deepcopy(DEFAULT_USER)
        default_user.update({'name': system.username, 'password': system.password})

        default_users = OrderedDict()
        default_users[internal_name(default_user['name'])] = default_user
        default_users[internal_name(GUEST_USER['name'])] = GUEST_USER

        super(Users, self).__init__(
            db_file='users.db',
            defaults=default_users
        )
        self._current_user = self[internal_name(GUEST_USER['name'])]

    ## Cookie Methods ##
    def log_in(self, username, password):
        """ Try to login user with provided username and password """
        logged_in = False
        # LOGGER.debug("username given = " + username)
        for user in self.values():
            # LOGGER.debug("server username = " + user['name'])
            if user['name'] == username and user['active']:
                # LOGGER.debug("password given = " + password)
                # LOGGER.debug("server password = " + user['password'])
                if user['password'] == password:
                    cookie_password = self._system_settings.cookie_password
                    response.set_cookie(
                        'current_user',
                        user['name'],
                        secret=cookie_password,
                        path='/'
                    )
                    self._current_user = user
                    logged_in = True

                    # LOGGER.debug("access = " + user['access'])
                break

        else:
            response.delete_cookie('current_user', path='/')
            self._current_user = self[internal_name(GUEST_USER['name'])]

        self._callbacks['update_user_panel']()

        return logged_in
       
    def log_out(self):
        """ Logs out current user """
        if not self._system_settings['user_bypass']:
            self.log_in(GUEST_USER['name'], GUEST_USER['password'])

    ## User Methods ##
    def current_user(self, user=None):
        """
        Either gets current user or set current user.

        :param user: If None provided, function will read current user.
            If user is provided, function will overwrite current user with user provided
        :return: Returns current user
        """
        if user is not None:
            self._current_user = user

        return self._current_user

    def get_user(self, user_key):
        """ Fetches particular user """
        if user_key in self.keys():
            return self[user_key]
        else:
            return copy.deepcopy(self.new_defaults)
       
    def load_user(self):
        """ Fetches current username from cookies """
        self._current_user = self[internal_name(GUEST_USER['name'])]

        cookie_password = self._system_settings.cookie_password
        username = request.get_cookie(
            'current_user',
            default=None,
            secret=cookie_password
        )
    
        # LOGGER.debug("username = " + str(username))
        
        if username:
            username = username.encode('ascii', 'ignore')
        
            for user in self.values():
                if user['name'] == username and user['active']:
                    self._current_user = user
                    self._callbacks['update_user_panel']()
                    break

    ## Cookie Data Methods ##   
    def update_current_user_cookies(self, update_dict, pre_format_cookies=False):
        """ Updates current user cookies """
        if pre_format_cookies:
            # LOGGER.debug("update_dict1 = " + str(update_dict))
            _format_cookies(update_dict)
            # LOGGER.debug("update_dict2 = " + str(update_dict))
        self._current_user['cookies'].update(update_dict)
        # LOGGER.debug("current_user['cookies'] = " + str(self.current_user['cookies']))
        self.save()
  
    ## Access Method ##
    def check_access(self, access_level, user=None):
        """ Checks if current access is above specified access level """       
        if user is None:
            user = self._current_user
        
        return bool(ACCESS[user['access']] >= ACCESS[access_level])

    def update_user(self, user_key, upd_dict):
        """ Update user with regards to current user cookies """
        # Update user
        if user_key in self.keys():
            if self._current_user == self[user_key]:
                if 'name' in upd_dict:
                    cookie_password = self._system_settings.cookie_password
                    response.set_cookie(
                        'current_user',
                        upd_dict['name'],
                        secret=cookie_password,
                        path='/'
                    )

                if 'access' in upd_dict:
                    self._current_user['access'] = upd_dict['access']
                    self._callbacks['update_user_panel']()
                    self._callbacks['select_user_panel']()

    ## Validation Methods ##
    def user_name_validation(self, address, username, access, active):
        """ Validate user ajax request """       
        json_dict = {}
        user_name_taken = False

        validate = NAME_FREE
        if not username:
            validate = NAME_EMPTY
        else:
            user_name_taken = self.name_taken(address, username)
            if user_name_taken:
                validate = NAME_TAKEN

        json_dict['form'] = self.validation_string + validate
        json_dict['user_name_taken'] = int(user_name_taken)
        json_dict['admin_present'] = int(self.admin_present(address, access, active))
        
        return json_dict

    def name_taken(self, current_user_key, prospective_name):
        """ Checks if username is taken already. Returns True or False """
        output = False

        for user_key, user in self.items():
            if user_key != current_user_key:
                if internal_name(user['name']) == internal_name(prospective_name):
                    output = True
                    break

        return output

    def admin_present(self, current_user_key, new_user_access, new_user_active):
        """ Checks if admin is present in the system. Returns True or False """
        present = False

        for user_key, user in self.items():
            access = user['access']
            active = user['active']
            if user_key == current_user_key:
                access = new_user_access
                active = new_user_active

            if ACCESS[access] >= ACCESS['admin'] and active:
                present = True
                break

        return present
