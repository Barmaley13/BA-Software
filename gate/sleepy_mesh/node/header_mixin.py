"""
Header Mixin Class
Contains header related methods

Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import copy
import logging

from py_knife.ordered_dict import OrderedDict

from gate.conversions import load_from_cookie


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class HeaderMixin(object):
    ## Overload Methods ##
    def read_headers(self, *args, **kwargs):
        """ Blank method should be over loaded by a parent class """
        LOGGER.error("Method 'read_headers' is not implemented!")
        raise NotImplementedError

    ## Headers, Header and Unit Selection Methods ##
    def live_units(self, cookie, header_name, *args, **kwargs):
        """ Returns currently selected units for the bar graph on live page """
        return self.__units(cookie, header_name, 'live', 'units', *args, **kwargs)

    def log_units(self, cookie, header_name, *args, **kwargs):
        """ Returns currently selected units for the bar graph on log page """
        return self.__units(cookie, header_name, 'log', 'units', *args, **kwargs)

    def live_table_units(self, cookie, header_name, *args, **kwargs):
        """ Returns currently selected list of units for the live page """
        return self.__units(cookie, header_name, 'live', 'table_units', *args, **kwargs)

    def log_table_units(self, cookie, header_name, *args, **kwargs):
        """ Returns currently selected list of units for the log page """
        return self.__units(cookie, header_name, 'log', 'table_units', *args, **kwargs)

    def __units(self, cookie, header_name, page_type, units_type, *args, **kwargs):
        """ Returns currently selected units for the bar graph on live page """
        output = None
        if units_type == 'table_units':
            output = OrderedDict()

        address = [
            'platforms', self['platform'], self['group'], 'headers', header_name, units_type]
        _cookie = load_from_cookie(cookie, address)

        header = None
        all_headers = self.read_headers('all', *args, **kwargs)
        for _header_name, _header in all_headers.items():
            if header_name == _header_name:
                header = _header
                break

        if header is not None:
            if _cookie is None:
                # Fetch default Header Cookie
                LOGGER.warning("Using default header cookie during '__units' execution!")
                # LOGGER.warning('address: {}'.format(address))
                # LOGGER.warning('cookie: {}'.format(cookie))
                _cookie = copy.deepcopy(header[page_type + '_cookie'])

            # Read portion
            if units_type == 'units':
                unit_index = _cookie[units_type]
                _output = header.units(unit_index)
                if _output is not None:
                    output = _output

            elif units_type == 'table_units':
                for unit_index in _cookie[units_type]:
                    _output = header.units(unit_index)
                    if _output is not None:
                        output[_output['internal_name']] = _output
        else:
            LOGGER.error("Header: " + str(header_name) + " does not exist!")

        return output
