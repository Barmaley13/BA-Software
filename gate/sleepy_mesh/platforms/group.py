"""
Group Class, contains list of nodes
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import os
import logging

from gate.conversions import internal_name
from gate.sleepy_mesh.error import NodeError

from base import PlatformBase
from nodes import GroupNodes


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Group(PlatformBase):
    def __init__(self, group_name, nodes, headers):
        self.system_settings = nodes.system_settings
        self._nodes = nodes

        db_file_prefix = None
        if headers is not None and internal_name(group_name) != 'inactive_group':
            db_file_prefix = os.path.join('platforms', headers['platform'], 'groups')

        super(Group, self).__init__(group_name, headers, db_file_prefix)

        db_file = None
        error_db_file = None
        if headers is not None:
            db_path = os.path.join('platforms', self['platform'], 'groups', self['internal_name'])
            db_file = os.path.join(db_path, 'nodes.db')
            error_db_file = os.path.join(db_path, 'default_error.db')

        self.nodes = GroupNodes(
            self._nodes,
            self.headers,
            db_file=db_file
        )

        self.error = NodeError(
            system_settings=self.system_settings,
            db_file=error_db_file
        )

    def save(self, db_content=None):
        """ Overloading default save method """
        self.nodes.save()
        super(Group, self).save()

    def delete(self):
        """ Overloading default delete method """
        self.nodes.delete()
        super(Group, self).delete()
