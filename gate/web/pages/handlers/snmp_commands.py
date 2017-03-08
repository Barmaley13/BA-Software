"""
SNMP Commands Web Handler with integrated Edit Methods
"""

### INCLUDES ###
from bottle import request

from gate.strings import VALIDATION_FAIL
from gate.conversions import internal_name, validate_ip_address, validate_oid

from gate.web.pages.handlers import WebHandlerOrderedDict


### CLASSES ###
class WebHandler(WebHandlerOrderedDict):
    def __init__(self, pages):
        super(WebHandler, self).__init__(pages, pages.manager.snmp_server.commands)

    def _update_command(self, command_key):
        """ Update/Create SNMP Commands """
        validate = True

        # Get data from forms
        command_name = request.forms.snmp_name.encode('ascii', 'ignore')
        command_type = request.forms.type.encode('ascii', 'ignore')
        command_oid = request.forms.oid.encode('ascii', 'ignore')
        value_type = request.forms.value_type.encode('ascii', 'ignore')
        command_value = request.forms.value.encode('ascii', 'ignore')

        # Validate
        validate &= (len(command_name) > 0)
        validate &= not(self._object.name_taken(command_key, command_name))
        validate &= validate_oid(command_oid)

        if value_type == 'integer' or value_type == 'time ticks':
            validate &= command_value.isdigit()
            if validate:
                command_value = int(command_value)
        elif value_type == 'OID':
            validate &= validate_oid(command_value)
        elif value_type == 'IP address':
            validate &= validate_ip_address(command_value)

        return_dict = {
            'kwargs': {},
            'save_cookie': validate
        }

        if validate:
            # Create save dictionary
            new_command_key = internal_name(command_name)
            save_dict = {
                'name': command_name,
                'type': command_type,
                'oid': command_oid,
                'value_type': value_type,
                'value': command_value
            }

            if command_key in self._object.keys():
                self._object[command_key].update(save_dict)

                if command_key != new_command_key:
                    self._object.insert_before(command_key, (new_command_key, save_dict))
                    del self._object[command_key]

                    # Update all SNMP tables
                    self._pages.platforms.update_snmp_dict('command', command_key, new_command_key)

            else:
                self._object[new_command_key] = save_dict

            new_cookie = self._pages.get_cookie()
            new_cookie['index'] = new_command_key
            return_dict['new_cookie'] = new_cookie
            self._object.save()

        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict

    def _test_command(self, command_key):
        """ Test (and saves) SNMP command """
        return_dict = self._update_command(command_key)
        if 'alert' not in return_dict['kwargs']:
            snmp_agent_key = request.forms.snmp_agent_key.encode('ascii', 'ignore')
            snmp_agent = self._manager.snmp_server.agents[snmp_agent_key]
            snmp_command = self._object[command_key]
            self._manager.snmp_server.queue.add(snmp_agent, snmp_command)

        return return_dict
