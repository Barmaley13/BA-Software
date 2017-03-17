"""
SNMP Agents Web Handler with integrated Edit Methods
"""

### INCLUDES ###
from bottle import request

from gate.strings import VALIDATION_FAIL
from gate.conversions import internal_name, validate_ip_address
from gate.snmp import SNMPAgent, SNMP_AGENT_DESCRIPTION

from gate.web.pages.handlers import WebHandlerOrderedDict


### CLASSES ###
class WebHandler(WebHandlerOrderedDict):
    def __init__(self, pages):
        super(WebHandler, self).__init__(pages, pages.manager.snmp_server.agents)

    def _update_agent(self, agent_key):
        """ Update/Create SNMP agents """
        validate = True

        # Get data from forms
        agent_name = request.forms.snmp_name.encode('ascii', 'ignore')
        ip_address = request.forms.ip_address.encode('ascii', 'ignore')
        port = int(request.forms.port)
        snmp_community = request.forms.snmp_community.encode('ascii', 'ignore')
        snmp_version = int(request.forms.snmp_version)

        # Validate
        validate &= (len(agent_name) > 0)
        validate &= not(self.name_taken(agent_key, agent_name))
        validate &= validate_ip_address(ip_address)

        return_dict = {
            'kwargs': {},
            'save_cookie': validate
        }

        if validate:
            # Create save dictionary
            new_agent_key = internal_name(agent_name)
            save_dict = {
                'name': agent_name,
                'ip_address': ip_address,
                'port': port,
                'snmp_community': snmp_community,
                'snmp_version': snmp_version
            }

            if agent_key in self._object.keys():
                if agent_key == new_agent_key:
                    self._object[agent_key].update(save_dict)
                else:
                    self._object.insert_before(agent_key, (new_agent_key, SNMPAgent(**save_dict)))
                    del self._object[agent_key]

                    # Update all SNMP tables
                    self._pages.platforms.update_snmp_dict('agent', agent_key, new_agent_key)

            else:
                self._object[new_agent_key] = SNMPAgent(**save_dict)

            new_cookie = self._pages.get_cookie()
            new_cookie['index'] = new_agent_key
            return_dict['new_cookie'] = new_cookie
            self._object.save()

        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict

    def _test_agent(self, agent_key):
        """ Test (and saves) SNMP agent """
        return_dict = self._update_agent(agent_key)
        if 'alert' not in return_dict['kwargs']:
            snmp_agent = self._object[agent_key]
            snmp_command = SNMP_AGENT_DESCRIPTION
            self._manager.snmp_server.queue.add(snmp_agent, snmp_command)

        return return_dict
