"""
Collection of Headers for different platforms
"""

### INCLUDES ###
import sys
import copy
import pkgutil
import logging

from base import Headers
from gate.common import GATE_FOLDER, HEADERS_FOLDER

from header.common import ADC_FIELDS, DISPLAY_FIELDS


### CONSTANTS ###
## Default Sensor Types ##
DEFAULT_SENSOR_TYPES = {
    'jowa': '1304',
    'swe': '1111'
}

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def generate_sensor_types(platform):
    """ Extracts platform type from platform string """
    # Figure out default sensor codes
    output = '1111'

    platform_list = platform.split('-')
    platform_company = platform_list[0]
    if len(platform_list) >= 3:
        output = platform_list[2]

    elif platform_company in DEFAULT_SENSOR_TYPES:
        output = DEFAULT_SENSOR_TYPES[platform_company]

    # LOGGER.debug('platform: {}'.format(platform))
    # LOGGER.debug('platform_company: {}'.format(platform_company))
    # LOGGER.debug('sensor_type: {}'.format(output))

    return output


def generate_node_headers(platform):
    """ Generates Headers Dynamically """
    # Figure out default sensor codes
    sensor_type = generate_sensor_types(platform)

    platform_company = platform.split('-')[0]

    # Import common module from headers
    sys.path.append(GATE_FOLDER)
    from headers import common

    headers = []
    for sensor_index, sensor_code in enumerate(sensor_type):
        channel_headers = []
        for importer, module_name, is_package in pkgutil.iter_modules([HEADERS_FOLDER]):
            if not is_package:
                header_name = module_name.split('.')[-1]
                # Load every module
                header_module = importer.find_module(module_name).load_module(module_name)
                if header_name.startswith(platform_company + '_'):
                    # Update header kwargs for this particular sensor index
                    header = copy.deepcopy(header_module.HEADER)

                    # Assign channel number (AKA data_field)
                    header['data_field'] = ADC_FIELDS[sensor_index]
                    header['sensor_code'] = header_name
                    # header['selected'] = bool(header_name == _header_name)

                    # Add platform related constants (do it only once!)
                    constants_name = platform_company.upper() + '_CONSTANTS'
                    if hasattr(common, constants_name):
                        constants = getattr(common, constants_name)

                        if 'constants' not in header['groups']:
                            header['groups']['constants'] = list()

                        header['groups']['constants'].extend(constants)

                    channel_headers.append(header)

        if len(channel_headers) > 1:
            multiple_header = copy.deepcopy(common.MULTIPLE)
            multiple_header['data_field'] = ADC_FIELDS[sensor_index]
            multiple_header['sensor_code'] = platform_company + '_ '

            channel_headers = [multiple_header] + channel_headers

        headers.append(channel_headers)

    # Add global headers
    headers += copy.deepcopy(common.HEADERS)

    # Add platform specific headers
    headers_name = platform_company.upper() + '_HEADERS'
    if hasattr(common, headers_name):
        common_headers = getattr(common, headers_name)
        headers += copy.deepcopy(common_headers)

    # Create headers instance
    output = Headers(headers, sensor_type)

    # LOGGER.debug('headers: {}'.format(headers))
    # LOGGER.debug('sensor_type: {}'.format(sensor_type))
    # LOGGER.debug('header keys: {}'.format(output.read('all', sensor_type).keys()))

    return output


def generate_system_headers():
    """ Generate System Headers """
    # Import system module from headers
    sys.path.append(GATE_FOLDER)
    from headers import system

    system_headers = copy.deepcopy(system.HEADERS)
    output = Headers(system_headers)

    return output
