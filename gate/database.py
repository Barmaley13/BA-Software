"""
Monkey Patch/Extend Database Classes
"""

### INCLUDES ###
import os
import copy
import logging

from py_knife.database import DatabaseEntry, DatabaseDictBase, DatabaseList, DatabaseDict, DatabaseOrderedDict

from gate.common import DATABASE_FOLDER

### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)
# LOGGER.setLevel(logging.DEBUG)


### MONKEY PATCH ###
## Init ##
def monkey_patched_init(self, entry_data_type, db_file=None, defaults=None, auto_load=True):
    self._main = entry_data_type()
    self._db_file = None
    if db_file is not None:
        self._db_file = os.path.join(DATABASE_FOLDER, db_file)
    self._defaults = defaults
    if auto_load:
        self.load()
    else:
        super(DatabaseEntry, self).__init__()


DatabaseEntry.__init__ = monkey_patched_init

## Debug Monkeying... ##

# Turn off auto key creation feature #
# def monkey_patched_init2(self, *args, **kwargs):
#     super(DatabaseDictBase, self).__init__(*args, **kwargs)
#     self.auto_key_creation = False
#
# DatabaseDictBase.__init__ = monkey_patched_init2


# Printing our saving procedures #
# old_save = DatabaseEntry.save
#
#
# def monkey_patched_save(self, *args, **kwargs):
#     if self._db_file is not None:
#         LOGGER.debug('Saving ' + str(self._db_file))
#
#     old_save(self, *args, **kwargs)
#
# DatabaseEntry.save = monkey_patched_save


### CLASSES ###
class ModifiedEntry(DatabaseEntry):
    def __init__(self, main_key, **kwargs):
        self.main_key = main_key
        super(ModifiedEntry, self).__init__(**kwargs)

    def _load(self):
        """ Internal Load - loads main from a file if it exists """
        self.main = type(self._main)()
        return super(ModifiedEntry, self)._load()

    ## Modifying Other Macros ##
    def __iter__(self):
        return iter(self.main)

    def __getitem__(self, key):
        """ Allows using self[key] method """
        return self.main[key]

    def __setitem__(self, key, value):
        """ Allows using self[key] = value method """
        super(ModifiedEntry, self).__setitem__(key, value[self.main_key])
        self.main[key] = value

    def __delitem__(self, key):
        """ Allows using del self[key] method """
        super(ModifiedEntry, self).__delitem__(key)
        del self.main[key]

    def __len__(self):
        """ Allows using len(self) method """
        return len(self.main)

    def __repr__(self):
        """ Allows using self method. Returns list of dictionaries """
        return repr(self.main)

    def __str__(self):
        """ Allows using print self method """
        return str(self.__repr__())

    def pop(self, index):
        """ Allows using pop method """
        super(ModifiedEntry, self).pop(index)
        return self.main.pop(index)


class ModifiedList(ModifiedEntry, DatabaseList):
    def _load_default(self):
        """ Loads main with defaults """
        # LOGGER.debug("type(defaults) = " + str(type(self._defaults)))

        if isinstance(self._defaults, type(self._main)):
            # LOGGER.debug("Shallow Copy")

            defaults = type(self._main)()
            for item in self._defaults:
                defaults.append(item[self.main_key])

            self.main = copy.copy(self._defaults)

        else:
            LOGGER.error("Defaults type: " + str(type(self._defaults)) + " is not supported!")
            defaults = None

        return defaults

    def save(self, db_content=None):
        """
        Overwriting default save method.
        :param db_content: This argument is included for compatibility with parent method.
        Please do not use this argument!

        :return: NA
        """
        for item in iter(self):
            item.save()

        super(ModifiedList, self).save()

    def delete(self):
        for item in iter(self):
            item.delete()

        # Save networks instance
        super(ModifiedList, self).delete()

    def append(self, value):
        """ Allows using append method """
        super(ModifiedList, self).append(value[self.main_key])
        self.main.append(value)

    def extend(self, value):
        """ Allows using extend method """
        super(ModifiedList, self).extend(value[self.main_key])
        self.main.extend(value)

    def insert(self, index, value):
        """ Allows using insert method """
        super(ModifiedList, self).insert(index, value[self.main_key])
        self.main.insert(index, value)


class ModifiedOrderedDict(ModifiedEntry, DatabaseOrderedDict):
    def _load_default(self):
        """ Loads main with defaults """
        # LOGGER.debug("type(defaults) = " + str(type(self._defaults)))

        if isinstance(self._defaults, type(self._main)):
            # LOGGER.debug("Shallow Copy")

            defaults = type(self._main)()
            for item_key, item_value in self._defaults.items():
                defaults[item_key] = item_value[self.main_key]

            self.main = copy.copy(self._defaults)

        else:
            LOGGER.error("Defaults type: " + str(type(self._defaults)) + " is not supported!")
            defaults = None

        return defaults

    def save(self, db_content=None):
        """
        Overwriting default save method.
        :param db_content: This argument is included for compatibility with parent method.
        Please do not use this argument!

        :return: NA
        """
        for item in self.values():
            item.save()

        super(ModifiedOrderedDict, self).save()

    def delete(self):
        for item in self.values():
            item.delete()

        super(ModifiedOrderedDict, self).delete()

    def update(self, value):
        """ Allows using update method """
        for item_key, item_value in value.items():
            self._main[item_key] = item_value[self.main_key]
        self.main.update(value)

    def items(self):
        """ Allows using items method """
        return self.main.items()

    def values(self):
        """ Allows using values method """
        return self.main.values()

    def keys(self):
        """ Allows using keys method """
        return self.main.keys()

    def clear(self):
        """ Allows using clear method """
        super(ModifiedOrderedDict, self).clear()
        return self.main.clear()

    def insert_after(self, existing_key, key_value):
        _key_value = (key_value[0], key_value[1][self.main_key])
        super(ModifiedOrderedDict, self).insert_after(existing_key, _key_value)
        self.main.insert_after(existing_key, key_value)

    def insert_before(self, existing_key, key_value):
        _key_value = (key_value[0], key_value[1][self.main_key])
        super(ModifiedOrderedDict, self).insert_before(existing_key, _key_value)
        self.main.insert_before(existing_key, key_value)
