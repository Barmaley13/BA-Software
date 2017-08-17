"""
Common Template Shortcuts
"""

### INCLUDES ###
import logging


### CONSTANTS ###
DATA_RATE = ['250 Kbps', '500 Kbps', '1 Mbps', '2 Mbps']
OFF_ON = ['Off', 'On']
BYTE_ORDER = ['Little Endian', 'Big Endian']
REGISTER_ORDER = ['Standard', 'Reversed']

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
## General cases ##
def checked(condition):
    """ Checks condition. If true returns checked """
    output = ""
    if condition:
        output = "checked"
    return output


def selected(condition):
    """ Checks condition. If true returns selected """
    output = ""
    if condition:
        output = "selected"
    return output


def get_options(options, selected_value):
    """ Returns options string """
    output = ""
    for index, option in enumerate(options):
        output += "<option value='" + str(index) + "' " + \
                  selected(selected_value == index) + " >" + \
                  str(option) + "</option>"
    return output


def hidden(condition):
    """ Checks condition. If true returns hidden html """
    output = ""
    if condition:
        output = "class='hidden'"
    return output


def disabled(condition):
    """ Checks condition. If true returns disabled """
    output = ""
    if condition:
        output = "disabled"
    return output


## Software Form ##
def form_extension(upload_type):
    """ Returns proper form extension depending on upload type """
    if upload_type == 'gate':
        extension = '.zip'
    else:
        extension = '.spy'
    return extension
