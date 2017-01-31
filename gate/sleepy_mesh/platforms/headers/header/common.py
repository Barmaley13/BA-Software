"""
Some common constants for this package
"""

### INCLUDES ###
import logging


### CONSTANTS ###
## Strings ##
OPEN_CIRCUIT = ' indicate that sensor circuit is open!'
SHORT_CIRCUIT = ' indicate that sensor circuit is shorted!'

MIN_ALARM = ' Min Alarm has been triggered!'
MAX_ALARM = ' Max Alarm has been triggered!'

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
## Misc Helpers ##
def fetch_item(item_dict, item_index):
    """
    :param item_dict: dictionary used for item fetch
    :param item_index: either item key or item index
    :return: Returns item
    """
    output = None

    item_type = type(item_index)
    if item_type is int:
        if item_index < len(item_dict):
            output = item_dict.values()[item_index]
        else:
            LOGGER.error("No such unit index during '_fetch_item' execution!")
    elif item_type in (str, unicode):
        unit_key = item_index.encode('ascii', 'ignore')
        if unit_key in item_dict.keys():
            output = item_dict[unit_key]
        else:
            LOGGER.error("No such unit key during '_fetch_item' execution!")
    else:
        LOGGER.error("Wrong item type: '" + str(item_type) + "' during '_fetch_item' execution!")

    return output
