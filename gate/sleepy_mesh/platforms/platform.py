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


### CONSTANTS ###
## Platform Naming Conventions ##
PLATFORM_NAMING_CONVENTIONS = {
    'jowa-102': 'Level Measurement',
    'swe-103': 'Default',
    'virgins': 'Virgin Hardware'
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

        super(Platform, self).__init__(name, platform_name, 'platforms')

        groups_db_file = None
        error_db_file = None
        if platform_name != 'virgins':
            db_path = os.path.join('platforms', platform_name)
            groups_db_file = os.path.join(db_path, 'groups.db')
            error_db_file = os.path.join(db_path, 'default_error.db')

        LOGGER.debug("Creating Default Groups")

        default_groups = OrderedDict()
        default_groups['inactive_group'] = Group('Inactive Group', platform_name, self._nodes)

        self.groups = Groups(
            self._nodes,
            platform_name,
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
