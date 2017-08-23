"""
Header Constant Class
"""

### INCLUDES ###
import logging

from base import HeaderBase


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class HeaderConstant(HeaderBase):
    """ Header Constant Class """

    def __init__(self, default_value, **kwargs):
        """
        Initializes header constant, done as part of Header initialization by using provided constant dictionary.

        :param default_value: Default value or a list of selectable values.
        :param measuring_units: Specify units that are used. Also displayed to user. Constant considered internal
            if units are not provided.
        :param description: Specify constant description. Also displayed to user.
        :param min_value: Minimum constant value or a formula to calculate it. Used for validation.
        :param max_value: Maximum constant value or a formula to calculate it. Used for validation.
        :param step: Step that are used during value selection of this constant.
        :param selected: Specify which constant is selected by default by specifying constant index.
            Note that list has to be provided for the default value in order for this argument to work properly.
        :return: Header Constant instance
        """
        defaults = {
            # Local Must Haves
            'default_value': default_value,
            # Internal
            '_external': bool(not ('measuring_units' not in kwargs and 'description' not in kwargs)),
            # Defaults
            'default_selected': 0,
            'measuring_units': None,
            'description': None,
            'min_value': 0,
            'max_value': 100,
            'step': 0.01
        }
        defaults.update(kwargs)

        super(HeaderConstant, self).__init__(**defaults)

    def default_value(self):
        """
        Constant method to return default value.

        :return: Default value of a constant
        """
        output = self['default_value']
        if type(output) is list and len(output):
            output = output[self['default_selected']]
        elif type(output) is str:
            output = None

        return output
