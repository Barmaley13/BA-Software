"""
Networks Related Intricacies
"""

### INCLUDES ###
from gate.database import ModifiedList

from .network import WebNetwork, NETWORK_UPDATE_TYPES, NETWORK_DEFAULTS


### CLASSES ###
class Networks(ModifiedList):
    """ Class responsible for a set of networks """

    def __init__(self, manager):
        self._manager = manager

        # FYI, parent class uses defaults to during load process
        # Therefore, default network list contains default network id and NOT default network instance!
        default_networks = list()
        default_networks.append(WebNetwork(self._manager))

        super(Networks, self).__init__(
            'net_id',
            db_file='networks.db',
            defaults=default_networks
        )

    ## Overwriting load/save methods ##
    def load(self):
        """
        Overwriting default load method.
        Load list does not contain network instances themselves, just network ids.
        This method uses those network ids to load network instances into networks list.

        :return: NA
        """
        super(Networks, self).load()

        if len(self._main):
            del self.main[:]
            # Normally, we would use provided network id to load network instances
            # But we do not use network id for anything since we have single network instance at the moment
            for network_id in self._main:
                self.main.append(WebNetwork(self._manager))
