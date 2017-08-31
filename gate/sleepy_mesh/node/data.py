"""
ADC Enables and Data Parsing Intricacies
"""

### INCLUDES ###
import logging

from gate.conversions import bin_to_int
from gate.sleepy_mesh.error import ADC_MISMATCH, ABSENT_NODE

from common import parse_raw_data
from headers import DISPLAY_FIELDS, DIAGNOSTIC_FIELDS
from diagnostics import NodeDiagnostics


### CONSTANTS ###
## Diagnostics Constants ##
DIAGNOSTIC_VALUES = (0.0, 100.0, 100.0, 0.0)

## Battery Monitor Conversions ##
BAT_MON = [1.70, 1.75, 1.80, 1.85, 1.90, 1.95, 2.00, 2.05, 2.10, 2.15, 2.20,
           2.25, 2.30, 2.35, 2.40, 2.45, 2.550, 2.625, 2.700, 2.775, 2.850, 2.925,
           3.000, 3.075, 3.150, 3.225, 3.300, 3.375, 3.450, 3.525, 3.600, 3.675]

## Battery Voltage Tracking ##
BATTERY_VOLTAGE_NUMBER = 2
BATTERY_THRESHOLD = 0.25

## Masks ##
RAW_DATA_ENABLES_MASK = 0x06FF  # Mask link quality
LQ_ENABLES_MASK = 0x0100

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def _get_mcu_temp(raw_temp):
    """ Function that converts raw temperature to temperature in degrees C """
    output = None
    if raw_temp is not None:
        temp_c = 1.13 * raw_temp - 272.8
        output = temp_c

    return output


def _get_bat_mon(raw_bat_mon):
    """ Function that converts raw battery monitor value to battery voltage """
    output = None
    if raw_bat_mon is not None and raw_bat_mon < len(BAT_MON):
        output = BAT_MON[raw_bat_mon]

    return output


def _lq_to_percent(link_quality):
    """ Converts link quality from (-)dBm to percentage """
    output = None
    if link_quality is not None:
        output = (127 - link_quality) * 100 / 127

    return output


### CLASSES ###
class NodeData(NodeDiagnostics):
    """ Extending Node class with NodeData portion """
    def __init__(self, system_settings, input_dict):
        # Initialize data
        if 'type' not in input_dict or input_dict['type'] == 'node':
            display_defaults = dict(zip(DISPLAY_FIELDS, (None,) * len(DISPLAY_FIELDS)))
            diagnostic_defaults = dict(zip(DIAGNOSTIC_FIELDS, DIAGNOSTIC_VALUES))

            input_dict.update({
                'new_data': False,
                'data_in': dict(display_defaults.items() + diagnostic_defaults.items()),
                '_battery_voltages': list()
            })

        super(NodeData, self).__init__(system_settings, input_dict)

    ## Private Methods ##
    # Upstream #
    def parse_data(self):
        """ Function that parses and processes data """
        if 'raw_data' in iter(self) and 'raw_lq' in iter(self):
            data_list = [None] * len(DISPLAY_FIELDS)

            self['new_data'] |= bool(self['raw_enables'])
            if self['new_data']:
                raw_data = self.pop('raw_data')
                self['new_data'] |= bool(len(raw_data))
                raw_data_enables = self['raw_enables'] & RAW_DATA_ENABLES_MASK
                if raw_data_enables:
                    position = 0
                    while position < len(data_list):
                        if raw_data_enables & 1:
                            # Check
                            # LOGGER.debug('position: ' + str(position))
                            # LOGGER.debug('len(raw_data): ' + str(len(raw_data)))

                            raw_arg, raw_data = parse_raw_data(raw_data)
                            data_list[position] = bin_to_int(raw_arg)

                            if data_list[position] is None:
                                self.error.set_error('node_fault', ADC_MISMATCH)
                                break

                        # Move to the next bit
                        raw_data_enables >>= 1
                        position += 1

                    # LOGGER.debug('data_list: ' + str(data_list))

                raw_lq_enables = self['raw_enables'] & LQ_ENABLES_MASK
                raw_lq = self.pop('raw_lq')
                if raw_lq_enables and raw_lq:
                    lq_index = DISPLAY_FIELDS.index('lq')
                    data_list[lq_index] = raw_lq

                # Data Post Processing
                data_list = self._parse_data(data_list)

            # Insert new data
            data_dict = dict(zip(DISPLAY_FIELDS, data_list))
            self['data_in'].update(data_dict)

        # Parse Diagnostics data
        super(NodeData, self).parse_data()

        if not self['presence']:
            # Nulls/Clears LQ (or Signal Strength) if the unit is missing
            self['data_in'].update({'lq': 0})

            # Set Error indicating node is absent
            self.error.set_error('generic', ABSENT_NODE)

        # Save error registers for future ack generation
        self.error.save_error_alarms()

    def check_battery(self, battery_voltage):
        """ Checks batteries, reset statistics if we get new battery """
        if self['presence']:
            if battery_voltage is not None:
                # Append to the list
                self['_battery_voltages'].append(battery_voltage)
                if len(self['_battery_voltages']) > BATTERY_VOLTAGE_NUMBER:
                    del self['_battery_voltages'][0]

                # Compare to threshold
                if len(self['_battery_voltages']) >= BATTERY_VOLTAGE_NUMBER:
                    if self['_battery_voltages'][-1] - self['_battery_voltages'][-2] >= BATTERY_THRESHOLD:
                        # Reset battery statistics
                        self._reset_current_draw()

                        LOGGER.warning("Resetting battery statistics of the node '" + str(self['name']) + "'!")

    ## Private Methods ##
    def _parse_data(self, data_list):
        """ Overload this method (if needed) """
        lq_index = DISPLAY_FIELDS.index('lq')
        temp_index = DISPLAY_FIELDS.index('temp')
        batt_index = DISPLAY_FIELDS.index('batt')

        data_list[lq_index] = _lq_to_percent(data_list[lq_index])
        data_list[temp_index] = _get_mcu_temp(data_list[temp_index])
        data_list[batt_index] = _get_bat_mon(data_list[batt_index])

        return data_list
