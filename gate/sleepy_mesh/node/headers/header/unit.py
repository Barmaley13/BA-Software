"""
Header Unit Class
"""

### INCLUDES ###
import logging

from gate.conversions import round_int

from variable import HeaderVariable
from common import MIN_ALARM, MAX_ALARM


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class HeaderUnit(HeaderVariable):
    """ ADC Unit Class"""

    def __init__(self, formula, **kwargs):
        """
        Initializes header unit, done as part of Header initialization by using provided unit dictionary.

        :param formula: formula to calculate this variable. You can use any internal constant names or
        internal variable names in this formula that have been declared earlier.
        :param measuring_units: Official unit name that will be displayed to user via web interface.
        :param min_value: Minimum constant value or a formula to calculate it. Used for validation.
        :param max_value: Maximum constant value or a formula to calculate it. Used for validation.
        :param str_format: Specify string formatting. Used for display and logs.
        :return: Header Unit instance
        """
        defaults = {
            # Local Must Haves
            'formula': formula,
            # Internal
            '_external': True,
            # Defaults
            'measuring_units': '',
            'min_value': 0,
            'max_value': 100,
            # Min Alarm
            'min_alarm_message': MIN_ALARM,
            # Max Alarm
            'max_alarm_message': MAX_ALARM,
            'step': 0.01,
            'str_format': '{0:.2f}'
        }
        defaults.update(kwargs)

        super(HeaderUnit, self).__init__(**defaults)

    # Fetch Value Methods
    def get_min(self, provider):
        """
        Get minimum value for the selected unit. Either fetch static value or calculate using internal formula.

        :param provider: data provider we are working with
        :return: minimum value for the selected unit.
        """
        return self._get_min_max('min', provider)

    def get_max(self, provider):
        """
        Get maximum value for the selected unit. Either fetch static value or calculate using internal formula.

        :param provider: data provider we are working with
        :return: maximum value for the selected unit.
        """
        return self._get_min_max('max', provider)

    def _get_min_max(self, selector, provider):
        """
        Internal shortcut for min/max value fetch/calculation

        :param selector: ``min`` or ``max``
        :param provider: data provider we are working with
        :return: min/max value
        """
        output = None

        if selector in ('min', 'max'):
            if self.enables(provider, 'const_set'):
                _selector_value = self[selector + '_value']
                if type(_selector_value) in (int, float):
                    # We have constant value!
                    output = _selector_value
                else:
                    # We have another constant or variable!
                    for node_field in ('constants', 'data_out'):
                        if _selector_value in provider[node_field][self['data_field']]:
                            output = provider[node_field][self['data_field']][_selector_value]
                            break

                if output is not None:
                    _rounding_scheme = {'min': 'floor', 'max': 'ceil'}
                    output = round_int(output, _rounding_scheme[selector], 0)

        return output

    def get_float(self, provider, data_in=None):
        """
        Fetches current value for the selected units if log data is not provided.
        Otherwise, applies formulas using provided data_in and fetches results dictionary.

        :param provider: data provider that we are working with
        :return: current value dictionary/calculated value dictionary using log data
        """
        output = None

        # if data_in is None:
        #     header_enable = self.enables(provider, 'live_enables')
        #     header_enable |= self.enables(provider, 'diagnostics')
        # else:
        #     header_enable = self.enables(provider, 'log_enables')

        header_enable = self.enables(provider, 'const_set')

        if header_enable:
            data_out = {}

            if data_in is None:
                data_out = provider['data_out'][self['data_field']]
            elif self['data_field'] in data_in:
                data_out = data_in[self['data_field']]

            if self['internal_name'] in data_out:
                output = data_out[self['internal_name']]

        return output

    def get_string(self, provider, data_in=None):
        """
        Fetches current value for the selected units if log data is not provided.
        Otherwise, applies formulas using provided data_in and fetches results dictionary.

        :param provider: data provider that we are working with
        :return: current value dictionary/calculated value dictionary using log data
        """
        output = self.get_float(provider, data_in)

        if output is not None:
            if type(self['str_format']) in (str, unicode):
                output = self['str_format'].format(output)
            else:
                output = self['str_format'](output)

        return output
