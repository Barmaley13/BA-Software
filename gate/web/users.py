"""
Users Related Intricacies
"""

### INCLUDES ###
import copy
import logging

from bottle import response, request

from ..database import DatabaseList


### CONSTANTS ###
## Access Constants ##
ACCESS = {
    'no_access': 0,
    'user': 10,
    'read': 20,
    'write': 30,
    'admin': 40
}

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
USERNAME_FREE = "*Username is available"
USERNAME_EMPTY = "*Username can not be empty!"
USERNAME_TAKEN = "*Username is taken already!"

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
class Users(DatabaseList):
    """ System related class """
    def __init__(self, callbacks, system):
        self._callbacks = callbacks
        self._system_settings = system

        # User Related #
        default_user = copy.deepcopy(DEFAULT_USER)
        default_user.update({'name': system.username, 'password': system.password})

        super(Users, self).__init__(
            db_file='users.db',
            # defaults=[default_user]
            defaults=[default_user, GUEST_USER]
        )
        self._current_user = GUEST_USER

    ## Cookie Methods ##
    def log_in(self, username, password):
        """ Try to login user with provided username and password """
        logged_in = False
        # LOGGER.debug("username given = " + username)
        for user in iter(self):
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
            self._current_user = GUEST_USER

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

    def get_user(self, user_index):
        """ Fetches particular user """
        if user_index < len(self):
            return self[user_index]
        else:
            return copy.deepcopy(NEW_USER_DEFAULTS)
       
    def load_user(self):
        """ Fetches current username from cookies """
        self._current_user = GUEST_USER

        cookie_password = self._system_settings.cookie_password
        username = request.get_cookie(
            'current_user',
            default=None,
            secret=cookie_password
        )
    
        # LOGGER.debug("username = " + str(username))
        
        if username:
            username = username.encode('ascii', 'ignore')
        
            for user in iter(self):
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

    def update_user(self, user_index, upd_dict):
        """ Update user with regards to current user cookies """
        # Create user
        if user_index >= len(self):
            user_index = -1
            self.append({})
            self[user_index].update(NEW_USER_DEFAULTS)

        # Update user
        if self._current_user == self[user_index]:
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

        self[user_index].update(upd_dict)

    ## Validation Methods ##
    def user_name_validation(self, address, username, access, active):
        """ Validate user ajax request """       
        json_dict = {}
        user_name_taken = False

        user_index = address['index']
        # LOGGER.debug('user_index: ' + str(user_index))

        validate = USERNAME_FREE
        if not username:
            validate = USERNAME_EMPTY
        else:
            user_name_taken = self.user_name_taken(user_index, username)
            if user_name_taken:
                validate = USERNAME_TAKEN

        json_dict['form'] = validate
        json_dict['user_name_taken'] = int(user_name_taken)
        json_dict['admin_present'] = int(self.admin_present(user_index, access, active))
        
        return json_dict

    def user_name_taken(self, user_index, user_name):
        """ Checks if username is taken already. Returns True or False """
        name_taken = False

        for index, user in enumerate(iter(self)):
            if index != user_index:
                if user['name'] == user_name:
                    name_taken = True
                    break

        return name_taken

    def admin_present(self, user_index, new_user_access, new_user_active):
        """ Checks if admin is present in the system. Returns True or False """
        present = False

        for index, user in enumerate(iter(self)):
            access = user['access']
            active = user['active']
            if index == user_index:
                access = new_user_access
                active = new_user_active

            if ACCESS[access] >= ACCESS['admin'] and active:
                present = True
                break

        return present