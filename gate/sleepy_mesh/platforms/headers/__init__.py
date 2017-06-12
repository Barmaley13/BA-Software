"""
Collection of Headers for different platforms
"""

### INCLUDES ###
import copy
import logging

from gate.sleepy_mesh.node import ADC_FIELDS

from base import NodeHeaders
import common


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def generate_node_headers(platform):
    """ Generates Headers Dynamically """
    output = None

    platform_list = platform.split('-')
    if len(platform_list) == 2:
        LOGGER.debug("platform = " + str(platform))

        platform_company = platform_list[0]
        platform_sensor_code = platform_list[1]

        headers_kwargs = {
            'platform': platform,
            'headers': common.HEADERS,
        }

        # Total count of repeating sensor indexes
        total_counter = {}
        for sensor_index in platform_sensor_code:
            if sensor_index not in total_counter:
                total_counter[sensor_index] = 0
            else:
                total_counter[sensor_index] += 1

        current_counter = {}
        for channel_number, sensor_index in enumerate(platform_sensor_code):
            # Current count of repeating sensor indexes
            if sensor_index not in current_counter:
                current_counter[sensor_index] = 1
            else:
                current_counter[sensor_index] += 1

            # Fetch header for this particular sensor index
            module_name = __name__ + '.' + platform_company + '_' + sensor_index
            LOGGER.debug("module name = " + str(module_name))
            try:
                header_module = __import__(module_name, fromlist=[''])
            except:
                LOGGER.warning('Could not find module named "' + str(module_name) + '" during header generation!')
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

        # Add some global/common data to header kwargs
        headers_name = platform_company.upper() + '_HEADERS'
        if hasattr(common, headers_name):
            headers = getattr(common, headers_name)
            headers_kwargs['headers'] += headers

        # Create headers with newly generated kwargs
        output = NodeHeaders(**headers_kwargs)
        LOGGER.debug("header keys = " + str(output.read('all').keys()))

    else:
        LOGGER.error('Platform name "' + str(platform) + '" can not be used for header generation!')

    return output
