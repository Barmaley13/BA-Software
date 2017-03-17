"""
Web Handler Module

Database Classes with Edit Method Extensions
Currently,
DatabaseList used by nodes, networks, users and virgins
DatabaseDict used by node, network, system, headers and web.pages
DatabaseOrderedDict used by nodes/platforms
"""

### INCLUDES ###
import logging

from bottle import request

from gate.strings import VALIDATION_FAIL
from gate.conversions import internal_name


### CONSTANTS ###
## Delays ##
REBOOT_DELAY = 3.0          # seconds

## Strings ##
NO_METHOD1 = "Edit method named "
NO_METHOD2 = " does not exist!"
NAME_FREE = ' name is available'
NAME_EMPTY = ' name can not be empty!'
NAME_TAKEN = ' name is taken already!'

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class WebHandlerBase(object):
    """ Handler that takes web request and modifies target instances """
    def __init__(self, pages, target_object):
        self._pages = pages
        self._manager = pages.manager
        self._object = target_object

    ## Edit Method Dispatcher ##
    def handle(self, cookie):
        """
        Edit method dispatcher assumes that::
        * All edit methods named similarly to "_up"
        * All edit methods are provided with index
        * All edit methods return validate and new_cookie values
        """
        return_dict = {
            'kwargs': {},
            'save_cookie': False,
            'new_cookie': None
        }

        action_method = request.forms.action_method.encode('ascii', 'ignore')
        LOGGER.debug("action_method = " + action_method + ", cookie = " + str(cookie))

        if type(cookie) is dict and 'index' in cookie:
            address = cookie['index']
        else:
            address = cookie

        if hasattr(self, '_' + action_method):
            edit_method = getattr(self, '_' + action_method)
            return_dict.update(edit_method(address))
        else:
            # Should never occur
            fail_message = NO_METHOD1 + action_method + NO_METHOD2
            LOGGER.error(fail_message)
            return_dict['kwargs']['alert'] = fail_message

        return return_dict

    def _cancel_software_update(self, *args):
        """ Just a buffer"""
        return_dict = {'kwargs': {}}

        self._manager.uploader.request_cancel_upload()

        return return_dict

    def _cancel_network_update(self, cookie):
        """ Cancel update on indexed network """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        self._manager.networks[0].request_cancel_update()

        return return_dict

    def _post_upload(self, cookie):
        """
        Confirmation from user is received.
        Trigger reboot to complete gate upload procedure
        """
        return_dict = {}

        if self._manager.reboot_flag:
            # Log Out
            self._pages.users.log_out()
            # Trigger Reboot
            self._manager.bridge.schedule(REBOOT_DELAY, self._manager.uploader.reboot_ack)

        return return_dict

    # FIXME: This should belong to JSON (or get_handlers)
    def name_validation(self, address, prospective_name, **kwargs):
        """ Validates prospective SNMP Agent/Command Name """
        json_dict = {}
        name_taken = False

        validate = NAME_FREE
        if not prospective_name:
            validate = NAME_EMPTY
        else:
            name_taken = self.name_taken(address, prospective_name)
            if name_taken:
                validate = NAME_TAKEN

        json_dict['form'] = self._object.validation_string + validate
        json_dict['name_taken'] = int(name_taken)

        return json_dict

    # FYI: This is shared by get and post handlers
    def name_taken(self, address, prospective_name):
        """ Checks if SNMP Agent/Command name is taken already. Returns True or False """
        output = False

        for object_key, object_value in self._object.items():
            if address != object_key:
                if internal_name(object_value['name']) == internal_name(prospective_name):
                    output = True
                    break

        return output


class WebHandlerList(WebHandlerBase):
    """ WebHandlerList with some generic edit methods """
    # TODO: Those methods assume that self._object is a list
    def _up(self, index):
        """ Move indexed value up """
        validate = index > 0

        return_dict = {
            'kwargs': {},
            'save_cookie': validate
        }

        if validate:
            # Up actually decrements index
            new_index = index - 1
            pop_item = self._object.pop(index)
            self._object.insert(new_index, pop_item)

            new_cookie = self._pages.get_cookie()
            new_cookie['index'] = new_index
            return_dict['new_cookie'] = new_cookie
            self._object.save()
        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict

    def _down(self, index):
        """ Move indexed value down """
        validate = index < (len(self._object) - 1)

        return_dict = {
            'kwargs': {},
            'save_cookie': validate
        }

        if validate:
            # Down actually increments index
            new_index = index + 1
            pop_item = self._object.pop(index)
            self._object.insert(new_index, pop_item)

            new_cookie = self._pages.get_cookie()
            new_cookie['index'] = new_index
            return_dict['new_cookie'] = new_cookie
            self._object.save()
        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict

    def _remove(self, index):
        """ Remove indexed value """
        validate = index < len(self._object)

        return_dict = {
            'kwargs': {},
            'save_cookie': validate
        }

        if validate:
            del self._object[index]

            return_dict['new_cookie'] = self._pages.default_cookie()
            self._object.save()
        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict


class WebHandlerOrderedDict(WebHandlerBase):
    """ WebHandlerOrderedDict with some generic edit methods """
    # TODO: Those methods assume that self._object is a OrderedDict
    def _up(self, object_key):
        """ Move indexed value up """
        object_index = self._object.keys().index(object_key)

        validate = object_index > 0

        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if validate:
            # Up actually decrements index
            insert_key = self._object.keys()[object_index - 1]
            object_value = self._object.pop(object_key)
            self._object.insert_before(insert_key, (object_key, object_value))

            self._object.save()
        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict

    def _down(self, object_key):
        """ Move indexed value down """
        object_index = self._object.keys().index(object_key)
        validate = object_index < (len(self._object) - 1)

        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if validate:
            # Down actually increments index
            insert_key = self._object.keys()[object_index + 1]
            object_value = self._object.pop(object_key)
            self._object.insert_after(insert_key, (object_key, object_value))

            self._object.save()
        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict

    def _remove(self, object_key):
        """ Remove indexed value """
        validate = object_key in self._object

        return_dict = {
            'kwargs': {},
            'save_cookie': validate
        }

        if validate:
            del self._object[object_key]

            return_dict['new_cookie'] = self._pages.default_cookie()
            self._object.save()
        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict
