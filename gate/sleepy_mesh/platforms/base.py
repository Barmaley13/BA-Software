"""
Platform Base Class
Base Class shared among Group and Platform Classes
"""

### INCLUDES ###
import os
import logging

from py_knife.pickle import unpickle_file

from gate.database import DatabaseDict
from gate.conversions import internal_name


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class PlatformBase(DatabaseDict):
    def __init__(self, name, headers, db_file_prefix, **kwargs):
        defaults = {
            'name': name,
            'internal_name': internal_name(name),
        }

        db_file = None
        self.headers = headers

        if self.headers is not None:
            if db_file_prefix is not None:
                db_file = os.path.join(db_file_prefix, defaults['internal_name'] + '.db')

            defaults.update({
                'platform': self.headers['platform'],
            })
        else:
            defaults.update({
                'platform': 'virgins',
            })

        defaults.update(kwargs)

        # LOGGER.debug("Defaults = " + defaults['name'])

        super(PlatformBase, self).__init__(
            db_file=db_file,
            defaults=defaults
        )

        # LOGGER.debug("Name = " + self['name'])

    def _load(self):
        """ Internal Load - loads main from a file if it exists """
        self.main = type(self._main)()

        if self._db_file is not None:
            database_data = unpickle_file(self._db_file)
            # LOGGER.debug('db_file = ' + str(self._db_file))
            if database_data is not False:
                # LOGGER.debug("Loading from file")
                return database_data

        if self._defaults is not None:
            # LOGGER.debug("Loading from defaults")

            super(PlatformBase, self).save(self._defaults)
            # LOGGER.debug("Saving to a file status: " + str(os.path.isfile(self._db_file)))

            return self._load_default()

        return None
