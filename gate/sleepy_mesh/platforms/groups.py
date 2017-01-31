"""
Groups is a list of group class instances
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import logging

from gate.database import ModifiedOrderedDict
from gate.conversions import external_name

from group import Group


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Groups(ModifiedOrderedDict):
    def __init__(self, nodes, headers, **kwargs):
        self.system_settings = nodes.system_settings
        self._nodes = nodes
        self.headers = headers
        super(Groups, self).__init__('internal_name', **kwargs)

    ## Overwriting load/save methods ##
    def load(self):
        """
        Overwriting default load method.
        Load list does not contain node instances themselves, just network addresses.
        This method uses those network addresses to load node instances into nodes dictionary.

        :return: NA
        """
        super(Groups, self).load()

        LOGGER.debug("Loading Groups")

        if self._db_file is not None:
            if len(self._main):
                self.main.clear()
                for group_name in self._main.values():
                    self.main[group_name] = Group(
                        external_name(group_name),
                        self._nodes,
                        self.headers,
                    )
