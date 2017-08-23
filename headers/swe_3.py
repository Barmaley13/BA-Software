# -*- coding: utf-8 -*-
"""
SWE Header, Code # 3
Generic On/Off switch. Shorting switch to 3.3V shows up as high value on the switch.
"""


### CONSTANTS ###
## Switch Units ##
SWITCH_STATE = {
    'name': 'Switch State',
    'formula': 'round(self/adc_max)',         # Positive polarity
    'measuring_units': 'on/off',
    'min_value': 0,
    'max_value': 1.0
}


## Headers Instance ##
HEADER = {
    'name': 'Switch',
    'groups': {
        'unit_list': [SWITCH_STATE]
    }
}
