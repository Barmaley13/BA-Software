"""
SNMP Commands Web Handler with integrated Edit Methods
"""

### INCLUDES ###
from bottle import request

from gate.strings import VALIDATION_FAIL
from gate.conversions import internal_name, validate_oid

from gate.web.pages.handlers import WebHandlerOrderedDict


### CLASSES ###
class WebHandler(WebHandlerOrderedDict):
    def __init__(self, pages):
        super(WebHandler, self).__init__(pages, pages.manager.snmp_server.traps)

    def _update_trap(self, trap_key):
        """ Update/Create SNMP Commands """
        validate = True

        # Get data from forms
        trap_name = request.forms.snmp_name.encode('ascii', 'ignore')
        trap_oid = request.forms.oid.encode('ascii', 'ignore')
        trap_value = request.forms.value.encode('ascii', 'ignore')

        # Validate
        validate &= (len(trap_name) > 0)
        validate &= not(self.name_taken(trap_key, trap_name))
        validate &= validate_oid(trap_oid)

        return_dict = {
            'kwargs': {},
            'save_cookie': validate
        }

        if validate:
            # Create save dictionary
            new_trap_key = internal_name(trap_name)
            save_dict = {
                'name': trap_name,
                'oid': trap_oid,
                'value': trap_value
            }

            if trap_key in self._object.keys():
                self._object[trap_key].update(save_dict)

                if trap_key == new_trap_key:
                    self._object[trap_key].update(save_dict)
                else:
                    self._object.insert_before(trap_key, (new_trap_key, save_dict))
                    del self._object[trap_key]

                    # Update all SNMP tables
                    self._pages.platforms.update_snmp_dict('trap', trap_key, new_trap_key)

            else:
                self._object[new_trap_key] = save_dict

            new_cookie = self._pages.get_cookie()
            new_cookie['index'] = new_trap_key
            return_dict['new_cookie'] = new_cookie
            self._object.save()

        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict
