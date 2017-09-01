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
    def live_units(self, cookie, header):
        """ Returns currently selected units for the bar graph on live page """
        return self.__units(cookie, header, 'live', 'units')

    def log_units(self, cookie, header):
        """ Returns currently selected units for the bar graph on log page """
        return self.__units(cookie, header, 'log', 'units')

    def live_table_units(self, cookie, header):
        """ Returns currently selected list of units for the live page """
        return self.__units(cookie, header, 'live', 'table_units')

    def log_table_units(self, cookie, header):
        """ Returns currently selected list of units for the log page """
        return self.__units(cookie, header, 'log', 'table_units')

    def __units(self, cookie, header, page_type, units_type):
        """ Returns currently selected units for the bar graph on live page """
        output = None
        if units_type == 'table_units':
            output = OrderedDict()

        address = [
            'platforms', self['platform'], self['group'], 'headers', header['internal_name'], units_type]
        _cookie = load_from_cookie(cookie, address)

        if _cookie is None:
            # Fetch default Header Cookie
            LOGGER.warning("Using default header cookie during '__units' execution!")
            # LOGGER.warning('address: {}'.format(address))
            # LOGGER.warning('cookie: {}'.format(cookie))
            _cookie = copy.deepcopy(header[page_type + '_cookie'])

        # Read portion
        if units_type == 'units':
            unit_index = _cookie[units_type]

            # # Multiple Hack
            # if unit_index == 'multiple':
            #     default_index = header[page_type + '_cookie'][units_type]
            #     unit_index = default_index

            _output = header.units(unit_index)
            if _output is not None:
                output = _output

        elif units_type == 'table_units':
            for index, unit_index in enumerate(_cookie[units_type]):

                # # Multiple Hack
                # if unit_index == 'multiple':
                #     default_indexes = header[page_type + '_cookie'][units_type]
                #     if index < len(default_indexes):
                #         unit_index = default_indexes[index]
                #     else:
                #         break

                _output = header.units(unit_index)
                if _output is not None:
                    output[_output['internal_name']] = _output

        return output
