"""
Collection of Headers for different platforms
"""

### INCLUDES ###
import copy
import logging

from gate.sleepy_mesh.node import ADC_FIELDS

from base import NodeHeaders
from common import JOWA_MAX, JOWA_REF, SWE_MAX, FLOATING_SWITCH
from common import GLOBAL_DIAGNOSTIC_HEADERS, JOWA_DIAGNOSTIC_HEADERS, SWE_DIAGNOSTIC_HEADERS, SWE_MCU_TEMP


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.ERROR)
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
            'display_headers': (),
            'diagnostics_headers': GLOBAL_DIAGNOSTIC_HEADERS
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
                sensor_headers = copy.deepcopy(header_module.HEADERS)
                LOGGER.debug("sensor_headers keys = " + str(sensor_headers.keys()))

                # Iterate over header kwargs
                for kwarg in headers_kwargs:
                    if kwarg in sensor_headers:
                        for header_index in range(len(sensor_headers[kwarg])):
                            # Modify name (if needed)
                            if total_counter[sensor_index]:
                                sensor_headers[kwarg][header_index]['name'] += ' ' + str(current_counter[sensor_index])
                                LOGGER.debug('header name = ' + sensor_headers[kwarg][header_index]['name'])

                            # Assign channel number (AKA data_field)
                            sensor_headers[kwarg][header_index]['data_field'] = ADC_FIELDS[channel_number]

                            # Add platform related constants (do it only once!)
                            if header_index == 0:
                                if 'constants' not in sensor_headers[kwarg][header_index]['groups']:
                                    sensor_headers[kwarg][header_index]['groups']['constants'] = list()
                                if platform_company == 'jowa':
                                    sensor_headers[kwarg][header_index]['groups']['constants'].append(JOWA_MAX)
                                    sensor_headers[kwarg][header_index]['groups']['constants'].append(JOWA_REF)
                                elif platform_company == 'swe':
                                    sensor_headers[kwarg][header_index]['groups']['constants'].append(SWE_MAX)

                            # Add floating switch variable (if needed)
                            if 'unit_list' not in sensor_headers[kwarg][header_index]['groups']:
                                sensor_headers[kwarg][header_index]['groups']['unit_list'] = list()
                            # sensor_headers[kwarg][header_index]['groups']['unit_list'].append(FLOATING_SWITCH)

                        headers_kwargs[kwarg] += sensor_headers[kwarg]

        # Add some global/common data to header kwargs
        if platform_company == 'jowa':
            headers_kwargs['diagnostics_headers'] += JOWA_DIAGNOSTIC_HEADERS
        elif platform_company == 'swe':
            headers_kwargs['display_headers'] += (SWE_MCU_TEMP, )
            headers_kwargs['diagnostics_headers'] += SWE_DIAGNOSTIC_HEADERS

        # Create headers with newly generated kwargs
        output = NodeHeaders(**headers_kwargs)
        LOGGER.debug("header keys = " + str(output.read('all').keys()))

    else:
        LOGGER.error('Platform name "' + str(platform) + '" can not be used for header generation!')

    return output