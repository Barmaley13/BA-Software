"""
Platform Class, list of platform class instances
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import copy
import logging

from py_knife.ordered_dict import OrderedDict

from gate.database import ModifiedOrderedDict
from gate.sleepy_mesh.node import Node

from platform import Platform
from group import Group


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Platforms(ModifiedOrderedDict):
    """ Class responsible for all nodes """
    def __init__(self, nodes):
        self.system_settings = nodes.system_settings
        self._nodes = nodes

        # FYI, default platforms dictionary should not contain any node instances
        # LOGGER.debug("Creating Default Platforms")

        default_platforms = OrderedDict()
        default_platforms['jowa-102'] = Platform('jowa-102', self._nodes)
        default_platforms['swe-103'] = Platform('swe-103', self._nodes)
        default_platforms['virgins'] = Platform('virgins', self._nodes)

        super(Platforms, self).__init__(
            'platform',
            db_file='platforms.db',
            defaults=default_platforms
        )

    def load(self):
        """ Load Platforms """
        super(Platforms, self).load()

        # LOGGER.debug("Loading Platforms")

        if self._db_file is not None:
            if len(self._main):
                self.main.clear()
                for platform_name in self._main.values():
                    # LOGGER.debug('Loading platform: ' + str(platform_name))
                    self.main[platform_name] = Platform(platform_name, self._nodes)

    def save(self, db_content=None):
        """ Save Platforms """
        self._nodes.save()
        super(Platforms, self).save()

    ## Create Node/Platform ##
    def create_node(self, input_dict):
        """ Creates new node and adds it to nodes list """
        node, platform_name = None, None

        if 'raw_platform' in input_dict:
            input_dict['platform'] = self.platform_match(input_dict, 'hw_type')

        if 'platform' in input_dict:
            platform_name = input_dict['platform']

        if platform_name is not None:
            if platform_name not in self.keys():
                # Create Platform
                # LOGGER.debug("Create Platform: " + str(platform_name))
                self[platform_name] = Platform(platform_name, self._nodes)

            # Create node
            LOGGER.debug('Creating Node: {}'.format(input_dict['net_addr']))

            node = Node(
                system_settings=self.system_settings,
                input_dict=input_dict
            )

            # LOGGER.debug('raw_platform: {}'.format(node['raw_platform']))
            # LOGGER.debug('platform: {}'.format(node['platform']))
            # LOGGER.debug('sensor_type: {}'.format(node['sensor_type']))
            # LOGGER.debug('headers: {}'.format(node.headers))

            # Update node error object
            node.error.update(copy.copy(self[platform_name].error))

            # Add node to platform inactive group
            net_addr = node['net_addr']
            self._nodes[net_addr] = node

            inactive_group = self[platform_name].groups.values()[0]
            node['group'] = inactive_group['internal_name']
            inactive_group.nodes[net_addr] = node

            # Disabling to speed things up
            # self.save()

        else:
            LOGGER.error('Can not create node - no platform information found!')

        return node

    ## Platform Match ##
    def platform_match(self, input_dict, match_field):
        """
        Matches specified field in output dict
        :param input_dict:
        :param match_field:
        :return:
        """
        output = None

        # Default platform
        platform_values = OrderedDict()
        platform_values['company'] = self.system_settings.name
        platform_values['hw_type'] = None
        platform_values['sensor_type'] = None

        # Split platform
        raw_platform_list = input_dict['raw_platform'].split('-')

        # Fill out fields
        for platform_index, platform_key in enumerate(platform_values.keys()):
            if platform_index < len(raw_platform_list):
                platform_values[platform_key] = raw_platform_list[platform_index]

        # Start matching procedure
        if match_field in platform_values and match_field != 'company':
            platform_parts = [platform_values['company']]
            if platform_values[match_field] is not None:
                platform_parts.append(platform_values[match_field])

            # Rebuild various platform names
            if match_field != 'sensor_type':
                platform_list = []
                for index in reversed(range(len(platform_parts))):
                    platform_list.append('-'.join(platform_parts[0:index + 1]))
            else:
                platform_list = ['-'.join(platform_parts)]

            # Match starting from specific to generic platform names
            for platform in reversed(platform_list):
                for platform_key in self.keys():
                    if match_field != 'sensor_type':
                        if platform == platform_key:
                            output = platform_key
                            break
                    else:
                        if platform in platform_key:
                            output = platform_key
                            break

                if output is not None:
                    break

            else:
                # Special Case
                if match_field == 'sensor_type':
                    # Generate new set of headers
                    output = platform_list[0]
        else:
            LOGGER.error('Match field: ' + str(match_field) + ' is not allowed!')

        return output

    ## Select Nodes ##
    def select_nodes(self, node_select):
        """ Returns dictionary of selected(all, active or inactive) nodes """
        return self._nodes.select_nodes(node_select)

    ## Delete Nodes ##
    def delete_node(self, node):
        """ Delete specified node """
        net_addr = node['net_addr']
        for platform_name, platform in self.items():
            if platform_name == node['platform']:
                for group_name, group in platform.groups.items():
                    if net_addr in group.nodes.keys():
                        del self[platform_name].groups[group_name].nodes[net_addr]

        del self._nodes[net_addr]
