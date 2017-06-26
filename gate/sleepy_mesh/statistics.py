"""
Sleepy Mesh Statistics Portion
"""


### INCLUDES ###
import copy
import logging

from base import SleepyMeshBase, SYNC_TYPES, LAST_SYNCS_NUMBER
from platforms.headers.base import Headers
from platforms.headers.system import HEADERS


### CONSTANTS ###
# Rolling Average Constants
SYNC_AVERAGE_LENGTH = 10

## Sleepy Mesh Statistics Defaults ##
STATISTICS_DEFAULTS = dict()
STATISTICS_DEFAULTS['name'] = 'System'
STATISTICS_DEFAULTS['data_in'] = dict()
STATISTICS_DEFAULTS['data_in']['recent_sync_rate'] = None
STATISTICS_DEFAULTS['data_in']['life_sync_rate'] = None
STATISTICS_DEFAULTS['data_in']['sync_current'] = None                      # Current Sync Processing Time
STATISTICS_DEFAULTS['data_in']['sync_average'] = None                      # Average Sync Processing Time
STATISTICS_DEFAULTS['data_in']['delay_current'] = None                     # Current Sync Delay
STATISTICS_DEFAULTS['data_in']['delay_average'] = None                     # Average Sync Delay
STATISTICS_DEFAULTS['data_out'] = dict()

## File Names ##
SYSTEM_STATISTICS_FILE = 'statistics.db'

## Strings ##
SYNC_BY = "Sync by "

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def _log_processing_time(processing_time_list, current_processing_time, processing_time_list_max_length):
    """ Logs processing time """
    if current_processing_time is not None:
        processing_time_list.append(current_processing_time)
        if len(processing_time_list) > processing_time_list_max_length:
            del processing_time_list[0]


def _rolling_average(processing_time_list):
    """ Calculates rolling average """
    output = None

    if len(processing_time_list):
        output = sum(processing_time_list) / len(processing_time_list)

    return output


### CLASSES ###
class SleepyMeshStatistics(SleepyMeshBase):
    def __init__(self, **kwargs):
        # Initialize Database Entry (to store various statistics data)
        # Sync Processing Times
        self._sync_start = None
        self._sync_stop = None

        # Statistics List
        self._node_processing_times = list()
        self._sync_processing_times = list()
        self._delay_times = list()

        # Internal Averages (for manual mode only!) #
        self.__sync_processing_times = list()
        self.__delay_times = list()

        # Create Headers
        self.headers = Headers(**HEADERS)

        system_defaults = copy.deepcopy(STATISTICS_DEFAULTS)
        headers_defaults = copy.deepcopy(self.headers.header_defaults)
        system_defaults.update(headers_defaults)

        # Create Database to store statistics
        super(SleepyMeshStatistics, self).__init__(
            db_file=SYSTEM_STATISTICS_FILE,
            defaults=system_defaults,
            auto_load=False,
            **kwargs
        )

        current_time = self.system_settings.time()
        system_defaults['created'] = current_time

        self.load()

        # Apply enables
        all_headers = self.headers.read('all').values()
        for header in all_headers:
            header.enables(self, 'const_set', True)

    ## Private Methods ##
    # Upstream #
    # Logging Specific Statistic Data
    def _clear_sync_times(self):
        """ Clears Sync Times """
        self._sync_start = None
        self._sync_stop = None

    def _log_sync_start_time(self, sync_start_time):
        """ Logs Sync Start Time """
        # LOGGER.debug('Logging sync start time')
        if self._mesh_awake:
            if self._sync_start is None:
                self._sync_start = sync_start_time

    def __log_sync_stop_time(self, sync_stop_time=None):
        """ Logs Sync Stop Time """
        # LOGGER.debug('Logging sync stop time')
        if sync_stop_time is None:
            sync_stop_time = self._ct_ls()

        self._sync_stop = sync_stop_time

    def _update_last_sync(self, callback_type='timeout'):
        """ Log sync stop time and proceed with updating last sync time """
        # LOGGER.debug('Logging sync stop time')
        self.__log_sync_stop_time()

        self._sync_type = callback_type

        # Send sync message to the web browser
        if self._sync_type in SYNC_TYPES:
            sync_sender = SYNC_TYPES[self._sync_type]
            self.websocket.send(SYNC_BY + sync_sender + self._ct_ls_str(self._sync_stop))
        else:
            LOGGER.error("SleepyMeshManager error, unknown sync type: " + str(self._sync_type) + "!")

        super(SleepyMeshStatistics, self)._update_last_sync()

    def _log_node_processing_time(self, node, start, stop):
        """ Log processing times """
        if node is not None:
            if stop > start:
                node_processing_time = stop - start

                if not self._mesh_awake:
                    if node['off_sync_time'] is None:
                        node['off_sync_time'] = node_processing_time

                LOGGER.debug('Start: ' + self._ct_ls_str(start)[1:] + ' Stop: ' + self._ct_ls_str(stop)[1:])

    # Overall Statistics Calculations
    def _update_statistics_data(self):
        """ Log Statistics Data """
        active_nodes = self.platforms.select_nodes('active')
        if len(active_nodes) > 0:
            self.error.save_error_alarms()

            self['data_in']['life_time'] = self.system_settings.time() - self['created']
            self['data_in']['recent_sync_rate'] = self.__calculate_sync_rate('recent_sync_rate')
            self['data_in']['life_sync_rate'] = self.__calculate_sync_rate('life_sync_rate')

            self['data_in']['sync_average'] = self.__calculate_sync_average(self._sync_processing_times)
            self['data_in']['delay_average'] = self.__calculate_delay_average(self._delay_times)

            LOGGER.debug('Current Sync Processing Time: ' + str(self['data_in']['sync_current']))
            LOGGER.debug('Current Sync Delay: ' + str(self['data_in']['delay_current']))
            LOGGER.debug('Average Sync Processing Time: ' + str(self['data_in']['sync_average']))
            LOGGER.debug('Average Sync Delay: ' + str(self['data_in']['delay_average']))

            self._calculate_current_draw()

            # Apply formulas on system headers
            headers = self.headers.read('diagnostics').values()
            for header in headers:
                header.apply_formulas(self)

    def _current_period(self):
        """ Calculate current period """
        current_period = None
        if len(self['last_syncs']) >= LAST_SYNCS_NUMBER:
            current_period = self['last_syncs'][-1] - self['last_syncs'][-2]

        return current_period

    def _calculate_current_draw(self, current_sync_time=None):
        """ Calculate current capacity draw for each node """
        current_period = self._current_period()

        if current_sync_time is None:
            current_sync_time = self['data_in']['sync_current']

        nodes = self.platforms.select_nodes('all')
        for node in nodes.values():
            if node.headers is not None:
                all_headers = node.headers.read('all').values()
                for header in all_headers:
                    if header['data_field'] == 'temp':
                        current_temp = header.units('celsius').get_float(node)
                        break
                else:
                    current_temp = None

                node.calculate_current_draw(current_period, current_sync_time, current_temp)

    ## Class-Private Methods ##
    def __calculate_sync_rate(self, sync_rate_type):
        """ Calculating sync rates, either recent_sync_rate or life_sync_rate """
        output = None

        active_nodes = self.platforms.select_nodes('active')
        nodes_number = len(active_nodes)

        if nodes_number > 0:
            sync_rate_sum = 0

            for node in active_nodes.values():
                header = node.headers.read('diagnostics')[sync_rate_type]
                node_sync_rate = header.units('percent').get_float(node)
                if node_sync_rate is not None:
                    sync_rate_sum += node_sync_rate

            output = int(sync_rate_sum / float(nodes_number))

        return output

    def __calculate_sync_average(self, sync_average_list):
        """ Calculating average sync processing time """
        sync_current = self['data_in']['sync_current']
        if self._sync_type == 'timeout' or sync_current is None:
            # Have to increase average in case of a timeout
            sync_current = self._wake_period()

        _log_processing_time(sync_average_list, sync_current, SYNC_AVERAGE_LENGTH)
        output = _rolling_average(sync_average_list)

        return output

    def __calculate_delay_average(self, delay_average_list):
        """ Calculating average delay time """
        output = None
        if self._sync_type != 'timeout':
            _log_processing_time(delay_average_list, self['data_in']['delay_current'], SYNC_AVERAGE_LENGTH)
            output = _rolling_average(delay_average_list)

        return output
