"""
Collection of Headers for different platforms
"""

### INCLUDES ###
import sys
import copy
import pkgutil
import logging

from base import NodeHeaders, Headers
from gate.common import GATE_FOLDER, HEADERS_FOLDER
from gate.sleepy_mesh.node import ADC_FIELDS


### CONSTANTS ###
DEFAULT_SENSOR_TYPES = {
    'jowa': '1203',
    'swe': '1111'
}
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def generate_node_headers(platform):
    """ Generates Headers Dynamically """
    output = None

    platform_company = platform.split('-')[0]
    if platform_company in DEFAULT_SENSOR_TYPES:
        sensor_codes = DEFAULT_SENSOR_TYPES[platform_company]

        headers_kwargs = {
            'platform': platform,
            'headers': list(),
        }

        # Import common module from headers
        sys.path.append(HEADERS_FOLDER)
        import common

        # Total count of repeating sensor indexes
        total_counter = {}
        for sensor_index in sensor_codes:
            if sensor_index not in total_counter:
                total_counter[sensor_index] = 0
            else:
                total_counter[sensor_index] += 1

        current_counter = {}
        for channel_number, sensor_index in enumerate(sensor_codes):
            # Current count of repeating sensor indexes
            if sensor_index not in current_counter:
                current_counter[sensor_index] = 1
            else:
                current_counter[sensor_index] += 1

            # Fetch header for this particular sensor index
            _header_name = platform_company + '_' + sensor_index
            LOGGER.debug("header name = " + str(_header_name))

            header_module = None
            for importer, module_name, is_package in pkgutil.iter_modules([HEADERS_FOLDER]):
                if not is_package:
                    header_name = module_name.split('.')[-1]
                    if header_name == _header_name:
                        header_module = importer.find_module(module_name).load_module(module_name)
                        break

            if header_module is None:
                LOGGER.warning('Could not find module named "' + str(_header_name) + '" during header generation!')
            else:
                # Update header kwargs for this particular sensor index
                headers = copy.deepcopy(header_module.HEADERS)

                # Update Headers
                for header_index, header in enumerate(headers):
                    # Modify name (if needed)
                    if total_counter[sensor_index]:
                        header['name'] += ' ' + str(current_counter[sensor_index])
                        LOGGER.debug('header name = ' + header['name'])

                    # Assign channel number (AKA data_field)
                    header['data_field'] = ADC_FIELDS[channel_number]

                    # Add platform related constants (do it only once!)
                    if header_index == 0:
                        if 'constants' not in header['groups']:
                            header['groups']['constants'] = list()

                        constants_name = platform_company.upper() + '_CONSTANTS'
                        if hasattr(common, constants_name):
                            constants = getattr(common, constants_name)
                            header['groups']['constants'].extend(constants)

                    # Add floating switch variable (if needed)
                    if 'unit_list' not in header['groups']:
                        header['groups']['unit_list'] = list()
                    # header['groups']['unit_list'].append(common.FLOATING_SWITCH)

                headers_kwargs['headers'] += headers

        if common is not None:
            # Add global/platform specific headers to kwargs
            headers_kwargs['headers'] += copy.deepcopy(common.HEADERS)

            headers_name = platform_company.upper() + '_HEADERS'
            if hasattr(common, headers_name):
                headers = getattr(common, headers_name)
                headers_kwargs['headers'] += headers

            # Create headers with newly generated kwargs
            output = NodeHeaders(**headers_kwargs)
            LOGGER.debug("header keys = " + str(output.read('all').keys()))

    else:
        LOGGER.error('Platform name "' + str(platform_company) + '" can not be used for header generation!')

    return output


def generate_system_headers():
    """ Generate System Headers """
    # Import system module from headers
    sys.path.append(GATE_FOLDER)
    import headers.system as system

    output = Headers(**system.HEADERS)

    return output
