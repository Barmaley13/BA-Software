"""
Log Functionality (of the node but could be anything else)
"""

### INCLUDES ###
import os
import glob
import logging

from py_knife import file_system, pickle
from py_knife.ordered_dict import OrderedDict

from gate.common import LOGS_FOLDER
from gate.database import DatabaseOrderedDict


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def update_log_timing(logs, time_diff):
    """
    Updates timing of each log
    :param logs: target logs
    :param time_diff: time difference
    :return:
    """
    for log_index, log_value in enumerate(logs):
        if 'time' in log_value:
            log_value[log_index]['time'] += time_diff


### CLASSES ###
class NodeLogs(DatabaseOrderedDict):
    def __init__(self, name, system_settings, **kwargs):
        # Private Members #
        self.name = name
        self._system_settings = system_settings

        # Overwriting log defaults
        kwargs['defaults'] = OrderedDict()
        kwargs['defaults']['logs'] = []               # Raw data stored as logs
        kwargs['defaults']['manual_log'] = False

        super(NodeLogs, self).__init__(**kwargs)

    ## Public Methods ##
    def files(self):
        """ Fetches db log files """
        output = glob.glob(os.path.join(LOGS_FOLDER, self.name + '*.db'))
        return output

    def manual_log(self):
        """ Enables manual logging (just for one log point) """
        self._main['manual_log'] = True

    def not_empty(self):
        """
        Logs Not Empty Flag
        :return: True - logs are not empty, False - logs are empty
        """
        output = bool(len(self.files()) or len(self._main['logs']))
        return output

    def clear(self):
        """
        Clear logs
        :return: return if logs were present before command execution
        """
        not_empty = self.not_empty()
        if not_empty:
            # Remove stored files on HD
            for item in self.files():
                file_system.remove_file(item)

            # Remove current logs
            del self._main['logs'][:]

            self.save()

        return not_empty

    ## Private Methods ##
    # Upstream #
    def dump(self):
        """ Checks if we need to dump logs """
        log_dump_status = None

        # LOGGER.debug("logs number = " + str(len(self._main['logs'])))
        if len(self._main['logs']) >= (2 * self._system_settings['log_limit']):
            log_dump_status = bool(self.__dump_logs())
            if log_dump_status:
                del self._main['logs'][0:self._system_settings['log_limit']]

                self.save()

        return log_dump_status

    def append(self, log_data):
        """ Appends logs """
        if not self._system_settings.manual_log or self._main['manual_log']:
            # LOGGER.debug('Logging!')
            self._main['logs'].append(log_data)

            # Reset Manual log flag
            if self._main['manual_log']:
                self._main['manual_log'] = False
        # else:
        #     LOGGER.debug('Not Logging!')

    def update_timing(self, time_diff):
        """ Updates log timing """
        # Update internal timing (created and logs fields)
        if len(self._main['logs']):
            update_log_timing(self._main['logs'], time_diff)
            self.save()

        # Update external log files
        for item_path in self.files():
            item_name = os.path.basename(item_path)
            logs = pickle.unpickle_file(os.path.join(LOGS_FOLDER, item_name))
            if logs is not False:
                if len(logs):
                    update_log_timing(logs, time_diff)

                    logs_name = self.__logs_name(logs)
                    if pickle.pickle_file(os.path.join(LOGS_FOLDER, logs_name), logs):
                        file_system.remove_file(item_path)
                else:
                    file_system.remove_file(item_path)

    ## Class-Private Methods ##
    def __dump_logs(self):
        """ Dumps logs to HD """
        logs_name = self.__logs_name(self._main['logs'])
        logs_path = os.path.join(LOGS_FOLDER, logs_name)
        logs_data = self._main['logs'][0:self._system_settings['log_limit']]
        return pickle.pickle_file(logs_path, logs_data)

    def __logs_name(self, logs):
        """ Creates name with time stamp for collection of logs """
        time_stamp = self._system_settings.log_file_time(logs[-1]['time'])
        logs_name = self.name + '_' + time_stamp + '.db'
        return logs_name

    # Overloading Generic Macros #
    def __iter__(self):
        return iter(self._main['logs'])

    def __getitem__(self, key):
        """ Allows using self[key] method """
        return self._main['logs'][key]

    def __setitem__(self, key, value):
        """ Allows using self[key] = value method """
        self._main['logs'][key] = value

    def __delitem__(self, key):
        """ Allows using del self[key] method """
        del self._main['logs'][key]

    def __len__(self):
        """ Allows using len(self) method """
        return len(self._main['logs'])

    def __repr__(self):
        """ Allows using self method. Returns list of dictionaries """
        return repr(self._main['logs'])

    def __str__(self):
        """ Allows using print self method """
        return str(self.__repr__())
