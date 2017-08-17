# -*- coding: utf-8 -*-
"""
SWE Header, Code # 1
Generic ADC Input
"""

### CONSTANTS ###
## ADC Percent Units ##
ADC_PERCENT = {
    'name': 'percent',
    'formula': 'self*100/adc_max',
    'measuring_units': '%',
    'min_value': 0,
    'max_value': 100
}


## Headers Instance ##
HEADERS = [
    {
        'name': 'ADC',
        'groups': {
            'unit_list': [ADC_PERCENT]
        }
    }
]
