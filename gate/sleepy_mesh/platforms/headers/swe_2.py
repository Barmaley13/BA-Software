# -*- coding: utf-8 -*-
"""
SWE Header, Code #2
Generic On/Off switch
"""

### INCLUDES ###
# from common import SHORT_CIRCUIT, OPEN_CIRCUIT


### CONSTANTS ###
## ADC Percent Units and Variables ##
SWITCH_STATE = {
    'name': 'Switch State',
    'formula': '1-round(self/adc_max)',         # Opposite polarity
    'measuring_units': 'on/off',
    'min_value': 0,
    'max_value': 1.0,
    # 'min_alarm': 0.5,
    # 'min_alarm_message': SHORT_CIRCUIT,
    # 'max_alarm': 0.5,
    # 'max_alarm_message': OPEN_CIRCUIT
}


## Headers Instance ##
HEADERS = [
    {
        'name': 'On/Off Switch',
        'groups': {
            'unit_list': [SWITCH_STATE]
        }
    }
]
