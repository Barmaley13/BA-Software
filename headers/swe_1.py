# -*- coding: utf-8 -*-
"""
SWE Header, Code # 1
Generic ADC Input
"""

### CONSTANTS ###
## ADC Units ##
ADC_VOLTAGE = {
    'name': 'voltage',
    'formula': 'self*1.6/adc_max',
    'measuring_units': 'V',
    'min_value': 0,
    'max_value': 1.6
}

ADC_PERCENT = {
    'name': 'percent',
    'formula': 'self*100/adc_max',
    'measuring_units': '%',
    'min_value': 0,
    'max_value': 100
}


## Headers Instance ##
HEADER = {
    'name': 'ADC',
    'groups': {
        'unit_list': [ADC_VOLTAGE, ADC_PERCENT]
    }
}
