"""
Capturing diagnostics data for the node
"""

### INCLUDES ###
import logging

from .base import NodeBase


### CONSTANTS ###
RECENT_SYNCS_NUMBER = 10

## Node Capacity Draw ##
DEFAULT_CURRENT_DRAW_TEMP = 25.0
SLEEP_DRAW = [(-20.0, 2.4e-6), (0.0, 2.5e-6), (25.0, 3.8e-6), (55.0, 7.6e-6)]
AWAKE_DRAW = [(-20.0, 6.6e-3), (0.0, 5.1e-3), (25.0, 3.5e-3), (55.0, 3.4e-3)]

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.ERROR)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class NodeDiagnostics(NodeBase):
    ## Public Methods ##
    def calculate_current_draw(self, current_period, current_sync_time, current_temp):
        """ Calculate current capacity draw for each node """
        if current_period is not None:
            # Calculate sleep and awake time for this period
            current_awake_time = 0
            if self['presence']:
                current_awake_time += current_sync_time

            if self['off_sync_time'] is not None:
                current_awake_time += self['off_sync_time']

            current_sleep_time = current_period - current_awake_time

            LOGGER.debug('current_sleep_time: ' + str(current_sleep_time))
            LOGGER.debug('current_awake_time: ' + str(current_awake_time))

            # Default Current Temperature (if needed)
            if current_temp is None:
                current_temp = DEFAULT_CURRENT_DRAW_TEMP

            LOGGER.debug('current_temp: ' + str(current_temp))

            # Getting interpolation values for currents sleep and awake draws
            _current_draw = dict()
            _current_draw['current_sleep_draw'] = None
            _current_draw['current_awake_draw'] = None
            interpolation_tables = [('current_sleep_draw', SLEEP_DRAW), ('current_awake_draw', AWAKE_DRAW)]
            for draw_key, interpolation_table in interpolation_tables:
                for point_index in range(len(interpolation_table)):
                    temp0, draw0 = interpolation_table[point_index]

                    if current_temp < temp0 and point_index == 0:
                        _current_draw[draw_key] = draw0
                        break

                    elif current_temp > temp0 and point_index == len(interpolation_table) - 1:
                        _current_draw[draw_key] = draw0
                        break

                    else:
                        temp1, draw1 = interpolation_table[point_index + 1]
                        if temp0 <= current_temp <= temp1:
                            _current_draw[draw_key] = (current_temp - temp0) * (draw1 - draw0) / \
                                                      (temp1 - temp0) + draw0
                            break

            LOGGER.debug('current_sleep_draw: ' + str(_current_draw['current_sleep_draw']))
            LOGGER.debug('current_awake_draw: ' + str(_current_draw['current_awake_draw']))

            # Calculating current draw
            if _current_draw['current_sleep_draw'] is not None and _current_draw['current_awake_draw'] is not None:
                current_draw = 0
                current_draw += current_sleep_time * _current_draw['current_sleep_draw']
                current_draw += current_awake_time * _current_draw['current_awake_draw']

                LOGGER.debug('current_draw: ' + str(current_draw))

                # Appending total draw of the node
                self['data_in']['total_draw'] += current_draw
                LOGGER.debug('total_draw: ' + str(self['data_in']['total_draw']))

        self['off_sync_time'] = None

    ## Private Methods ##
    # Upstream #
    def parse_data(self):
        """ Updating diagnostics data """
        life_time = self.system_settings.time() - self['created']
        self['data_in']['life_time'] = life_time
        self['constants']['total_draw']['life_time'] = life_time

        # Gather diagnostics data #
        self['constants']['recent_sync_rate']['recent_syncs'].append(int(self['presence']))

        if len(self['constants']['recent_sync_rate']['recent_syncs']) > RECENT_SYNCS_NUMBER:
            del self['constants']['recent_sync_rate']['recent_syncs'][0]

        if self['presence']:
            self['constants']['life_sync_rate']['successful_syncs'] += 1

        self['constants']['life_sync_rate']['total_syncs'] += 1

    def _reset_current_draw(self):
        """ Resets current draw """
        self['data_in']['total_draw'] = 0.0
