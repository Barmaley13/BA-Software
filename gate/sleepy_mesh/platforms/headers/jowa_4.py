# -*- coding: utf-8 -*-
"""
Jowa Header, Code #4
4-20 Input
"""

### IMPORTS ###
from common import SHORT_CIRCUIT, OPEN_CIRCUIT


### CONSTANTS ###
## 4-20 Constants ##
M4 = {
    'name': 'M4',
    'default_value': 4.0,
    'measuring_units': '',
    'description': 'Measurement corresponding to 4mA current, lowest end of the range',
    'min_value': -10000,
    'max_value': 10000,
    'step': 0.001
}

M20 = {
    'name': 'M20',
    'default_value': 20.0,
    'measuring_units': '',
    'description': 'Measurement corresponding to 20mA current, highest end of the range',
    'min_value': -10000,
    'max_value': 10000,
    'step': 0.001
}

# TODO: Move to common?
MU = {
    'name': 'Measuring Units',
    'default_value': ['', 'mA', 'V', '%', 'meters', 'feet', 'liters', u'KLiters (m³)', 'gallons',
                      'KGallons', u'°C', u'°F'],
    'measuring_units': '',
    'description': 'Please specify measurement units for you own reference. This will change units globally!'
}

# Internal Current Sampling Resistance AKA R420
R420 = {
    'name': 'R420',
    'default_value': 100        # Actual value
    # 'default_value': 0.01     # FOR TESTING ON DEFAULT NODE ONLY!
}

## 4-20 Variables and Units ##
# 4-20 calculation notes:
# M = I420 * LFSF + LFO
# LFSF = (M20 - M4)/(20mA - 4mA)
# LFO = M4 - 4mA*LFSF
# I420 = V420/R420
# V420 = (ADC/ADCmax)*Vref
# M = (((ADC/ADCmax)*Vref)/R420)*LFSF + LFO
# Where,
# M, Measurement in whatever units that might be
# I420, 4-20 Current
# V420, ADC Input Voltage
# R420, Current Sampling Resistance
# LSF, Linear Function Scale Factor
# LFO, Linear Function Offset
# ADC, Current value of ADC (read DB value for that)
# ADCmax, Max value of ADC => 0xFFFFFF = 16777215
# Vref, ADC Voltage Reference (Currently 2.5V)
LFSF = {
    'name': 'lfsf',
    'formula': '(m20 - m4)/0.016'
}
LFO = {
    'name': 'lfo',
    'formula': 'm4 - 0.004*lfsf'
}
I420 = {
    'name': 'Current',
    'formula': '(((self/adc_max)*adc_ref)/r420)',
    'min_alarm': 0.002,
    'min_alarm_message': SHORT_CIRCUIT,
    'max_alarm': 0.040,
    'max_alarm_message': OPEN_CIRCUIT
}
MEASUREMENT = {
    'name': 'measurement',
    'formula': 'current*lfsf + lfo',
    'measuring_units': '',
    'min_value': 'm4',
    'max_value': 'm20'
}


## Headers Instance ##
HEADERS = {
    'display_headers': (
        {
            'name': '4-20 Input',
            'groups': {
                'constants': [M4, M20, MU, R420],
                'variables': [LFSF, LFO, I420],
                'unit_list': [MEASUREMENT]
            }
        },
    )
}
