"""
Platform Class, contains list of groups
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import os
import logging

from py_knife.ordered_dict import OrderedDict

from gate.sleepy_mesh.error import NodeError

from base import PlatformBase
from group import Group
from groups import Groups
from headers import generate_node_headers


### CONSTANTS ###
## Platform Naming Conventions ##
PLATFORM_NAMING_CONVENTIONS = {
    'virgins': 'Virgin Hardware',
    'jowa-102': 'Level Measurement',
    'swe-103': 'Default'
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Platform(PlatformBase):
    def __init__(self, platform_name, nodes):
        self.system_settings = nodes.system_settings
        self._nodes = nodes

        if platform_name in PLATFORM_NAMING_CONVENTIONS:
            name = PLATFORM_NAMING_CONVENTIONS[platform_name]
        else:
            name = str(platform_name) + ' Platform'

        headers = None
        groups_db_file = None
        error_db_file = None
        if platform_name != 'virgins':
            headers = generate_node_headers(platform_name)
            db_path = os.path.join('platforms', platform_name)
            groups_db_file = os.path.join(db_path, 'groups.db')
            error_db_file = os.path.join(db_path, 'default_error.db')

        super(Platform, self).__init__(name, headers, 'platforms')

        # Assign header information to all the nodes that belong to this platform (if needed)
        for net_addr, node in self._nodes.items():
            if node.headers is None:
                if node['platform'] == self['platform']:
                    node.headers = self.headers

        LOGGER.debug("Creating Default Groups")

        default_groups = OrderedDict()
        default_groups['inactive_group'] = Group('Inactive Group', self._nodes, self.headers)

        self.groups = Groups(
            self._nodes,
            self.headers,
            db_file=groups_db_file,
            defaults=default_groups
        )

        self.error = NodeError(
            system_settings=self.system_settings,
            db_file=error_db_file
        )

    def save(self, db_content=None):
        """ Overloading default save method """
        self.groups.save()
        super(Platform, self).save()

    def delete(self):
        """ Overloading default delete method """
        self.groups.delete()
        super(Platform, self).delete()
