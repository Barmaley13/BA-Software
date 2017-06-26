"""
Modbus Error Mixin
"""

### INCLUDES ###
import logging

from base import BaseError


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class ModbusError(BaseError):
    ## Public Methods ##
    def modbus_status(self):
        """ Prepares node status data to fetch via modbus server """
        modbus_status = []
        modbus_status1 = self['error']['_alarms']['generic'] & 0x00FF
        modbus_status1 |= (self['error']['_alarms']['sensor_fault_min_alarm'] & 0x000F) << 8
        modbus_status1 |= (self['error']['_alarms']['sensor_fault_max_alarm'] & 0x000F) << 12
        modbus_status.append(modbus_status1)
        modbus_status2 = self['error']['_alarms']['alarms_min_alarm'] & 0x00FF
        modbus_status2 |= (self['error']['_alarms']['alarms_max_alarm'] & 0x00FF) << 8
        modbus_status.append(modbus_status2)

        return modbus_status
