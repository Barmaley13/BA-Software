"""
Group Nodes Class
Just a list of nodes that belong to a particular group
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import logging

from gate.database import ModifiedOrderedDict


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class GroupNodes(ModifiedOrderedDict):
    def __init__(self, nodes, **kwargs):
        self.system_settings = nodes.system_settings
        self._nodes = nodes

        super(GroupNodes, self).__init__('net_addr', **kwargs)

    ## Overloading load/save methods ##
    def load(self):
        """
        Overwriting default load method.
        Load list does not contain node instances themselves, just network addresses.
        This method uses those network addresses to load node instances into nodes dictionary.

        :return: NA
        """
        super(GroupNodes, self).load()

        if self._db_file is not None:
            if len(self._main):
                self.main.clear()
                for net_addr in self._main.values():
                    if net_addr in self._nodes.keys():
                        self.main[net_addr] = self._nodes[net_addr]

                    else:
                        LOGGER.warning("Deleting node with net_addr '" + str(net_addr) + "' from the group!")

                        _main_key = self._main.keys()[self._main.values().index(net_addr)]
                        del self._main[_main_key]

    def save(self, db_content=None):
        """ Overwriting default save method """
        super(ModifiedOrderedDict, self).save()
