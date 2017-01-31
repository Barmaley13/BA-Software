"""
Alerts and Acks Web Handler
"""


### INCLUDES ###
import logging

from bottle import request

from py_knife.ordered_dict import OrderedDict

from gate.web.pages.handlers import WebHandlerBase


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class WebHandler(WebHandlerBase):
    def __init__(self, pages):
        super(WebHandler, self).__init__(pages, pages.manager)

    # Generic #
    def _update(self, address):
        """ Update SNMP Alerts and Acks """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        active_platforms = self._pages.platforms.active_platforms()
        if len(active_platforms):
            # Generate some "constants"
            snmp_groups = OrderedDict()
            snmp_groups['agent'] = self._manager.snmp_server.agents
            snmp_groups['set'] = self._manager.snmp_server.commands
            snmp_groups['clear'] = self._manager.snmp_server.commands
            snmp_groups['trap'] = self._manager.snmp_server.traps

            # Find target using address
            if 'nodes' in address:
                target = self._pages.platforms.node(address)
            elif 'group' in address:
                target = self._pages.platforms.group(address)
            elif 'platform' in address:
                target = self._pages.platforms.platform(address)
            else:
                target = active_platforms.values()[0]

            alert_messages = target.headers.alert_messages('all')
            for alert_key in alert_messages.keys():
                # Get Error field and error code
                alert_key_list = alert_key.split('-')
                error_field = alert_key_list[0]
                error_code = alert_key_list[1]

                # Get SNMP Dict
                snmp_dict = dict()
                for snmp_key, snmp_items in snmp_groups.items():
                    snmp_form_key = alert_key + '-' + snmp_key
                    snmp_item_key = request.forms.get(snmp_form_key).encode('ascii', 'ignore')

                    # LOGGER.debug('SAVE: ' + snmp_form_key + " : " + snmp_item_key)

                    if len(snmp_item_key):
                        if snmp_item_key in snmp_items.keys():
                            snmp_dict[snmp_key] = snmp_item_key
                    elif snmp_item_key == '':
                        snmp_dict[snmp_key] = None

                # Update Defaults/Specific Node
                targets = [target]

                # Update Nodes
                if 'nodes' in address:
                    pass
                elif 'group' in address:
                    for node in target.nodes.values():
                        targets.append(node)
                elif 'platform' in address:
                    for group in target.groups.values():
                        targets.append(group)
                        for node in group.nodes.values():
                            targets.append(node)

                for _target in targets[::-1]:
                    _target.error.set_snmp(error_field, error_code, snmp_dict)
                    _target.error.save()
                    _target.save()

        return return_dict
