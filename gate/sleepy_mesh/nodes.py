"""
Nodes Related Intricacies
"""

### INCLUDES ###
import logging

from py_knife.ordered_dict import OrderedDict

from gate.database import ModifiedOrderedDict
from gate.modbus import MODBUS_REG_NUM

from node import Node


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Nodes(ModifiedOrderedDict):
    """ Class responsible for all nodes """
    def __init__(self, system_settings):
        self.system_settings = system_settings

        super(Nodes, self).__init__(
            'net_addr',
            db_file='nodes.db',
        )

    ## Overwriting load/save methods ##
    def load(self):
        """
        Overwriting default load method.
        Load list does not contain node instances themselves, just network addresses.
        This method uses those network addresses to load node instances into nodes dictionary.

        :return: NA
        """
        super(Nodes, self).load()

        if self._db_file is not None:
            if len(self._main):
                self.main.clear()
                for net_addr in self._main:
                    input_dict = {'net_addr': net_addr}

                    self.main[net_addr] = Node(
                        system_settings=self.system_settings,
                        input_dict=input_dict,
                    )

    def save(self, db_content=None):
        """ Overwriting default save method """
        for node in self.main.values():
            # Hopefully this will speed up execution
            if node['presence']:
                node.save()

        super(ModifiedOrderedDict, self).save()

    ## External Methods ##
    def reset_flags(self):
        """ Resets presence flags for all nodes """
        for net_addr, node in self.items():
            node.reset_flags()

    def select_nodes(self, node_select):
        """ Returns dictionary of selected(all, active or inactive) nodes """
        nodes_dict = OrderedDict()

        for net_addr, node in self.items():
            selected = False

            if node_select == 'ALL':
                selected = True
            elif node_select == 'all':
                selected = bool(node['type'] != 'virgin')
            elif node_select == 'virgins':
                selected = bool(node['type'] == 'virgin')
            elif node_select == 'active':
                selected = not node['inactive']
            elif node_select == 'inactive':
                selected = node['inactive']

            if selected:
                nodes_dict[net_addr] = node

        return nodes_dict

    def modbus_address(self):
        """
        Provides node with modbus address

        :return: Modbus Address
        """
        modbus_addresses = self.modbus_addresses()

        # print('modbus_addresses: {}'.format(modbus_addresses))

        modbus_address = 0
        if len(modbus_addresses) > 0:
            modbus_address = modbus_addresses[-1] + MODBUS_REG_NUM

        return modbus_address

    def modbus_addresses(self):
        """
        :return: Sorted Modbus Addresses
        """
        modbus_addresses = list()
        nodes = self.select_nodes('active').values()

        for node in nodes:
            if node['modbus_addr'] is not None:
                if node['modbus_addr'] not in modbus_addresses:
                    modbus_addresses.append(node['modbus_addr'])

        modbus_addresses.sort()

        return modbus_addresses
