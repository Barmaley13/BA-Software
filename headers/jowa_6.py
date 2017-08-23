# -*- coding: utf-8 -*-
"""
JOWA Header, Code # 6
Generic On/Off switch. Shorting switch to ground shows up as high value on the switch.
"""


### CONSTANTS ###
## Switch Units ##
SWITCH_STATE = {
    'name': 'Switch State',
    'formula': '1-round(self/adc_max)',       # Negative polarity
    'measuring_units': 'on/off',
    'min_value': 0,
    'max_value': 1.0
}


## Headers Instance ##
HEADER = {
    'name': 'Floating Switch',
    'groups': {
        'unit_list': [SWITCH_STATE]
    }
}
