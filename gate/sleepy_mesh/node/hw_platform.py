"""
Platform Class
"""

### INCLUDES ###
import logging

from gate.sleepy_mesh.error import ADC_EOC, ADC_EXR, ADC_SIG, NODE_MESSAGES

from headers import ADC_FIELDS
from data import NodeData


### CONSTANTS ###
## Masks ##
EOC_MASK = 0x08000000
EXR_MASK = 0x01000000
SIG_MASK = 0x02000000


## Strings ##
MEASURING = " measuring "

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.ERROR)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class NodePlatform(NodeData):
    ## Private Methods ##
    # ADC Parsers #
    # (Include if LTC2404 is present on the node/platform)
    # TODO: Move this back to the Node code!
    def _parse_data(self, data_list):
        """ Converts raw adc data with errors and extra bits to pure raw adc data """
        if self['platform'] is not None:
            if 'jowa' in self['platform']:
                for index, field in enumerate(ADC_FIELDS):
                    adc_data = data_list[index]
                    if adc_data is not None:
                        # Get rid off SUB LSBs bits
                        adc_data = ((adc_data >> 4) & 0x0FFFFFFF)

                        # Parse error data
                        if (adc_data & (EOC_MASK | EXR_MASK)) or not (adc_data & SIG_MASK):
                            if adc_data & EOC_MASK:
                                error_message = NODE_MESSAGES[ADC_EOC] + MEASURING + str(field)
                                self.error.set_error('node_fault', ADC_EOC, error_message)
                                LOGGER.error("ADC EOC!")
                            elif adc_data & EXR_MASK:
                                error_message = NODE_MESSAGES[ADC_EXR] + MEASURING + str(field)
                                self.error.set_error('node_fault', ADC_EXR, error_message)
                                LOGGER.error("ADC EXR!")
                            elif not (adc_data & SIG_MASK):
                                error_message = NODE_MESSAGES[ADC_SIG] + MEASURING + str(field)
                                self.error.set_error('node_fault', ADC_SIG, error_message)
                                LOGGER.error("ADC SIG!")

                            data_list[index] = None
                        else:
                            # Get rid off error data
                            data_list[index] = float(adc_data & 0x00FFFFFF)

        LOGGER.debug("Node[" + self['net_addr'] + "] = " + str(data_list))

        return super(NodePlatform, self)._parse_data(data_list)
