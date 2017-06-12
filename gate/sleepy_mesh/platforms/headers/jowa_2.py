# -*- coding: utf-8 -*-
"""
Jowa Header, Code #2
Temperature
"""

### INCLUDES ###
from common import FAHRENHEIT, OPEN_CIRCUIT, SHORT_CIRCUIT


### CONSTANTS ###
## Temperature Constants ##
# External DTL
DTL = {
    'name': 'DTL',
    'default_value': 19.4,
    'measuring_units': 'meters',
    'description': 'Distance from sensor "zero" to Temperature element',
    'min_value': 0.0,
    'max_value': 49.9,
    'step': 0.001
}

# Internal DTL
# DTL = {
#     'name': 'DTL',
#     'default_value': 0
# }

ZT = {
    'name': 'ZT',
    'default_value': 0,
    'measuring_units': u'°C',
    'description': 'Zero Level (offset adjustment)',
    'min_value': -10,
    'max_value': 10,
    'step': 0.001
}
# External RPT
# RPT = {
#     'name': 'RPT',
#     'default_value': 4020,
#     'measuring_units': 'ohms',
#     'description': 'Value of temperature pull up resistor',
#     'min_value': 500,
#     'max_value': 1000000,
#     'step': 1
# }
# Internal RPT
RPT = {
    'name': 'RPT',
    'default_value': 4020
}


## Temperature Units and Variables ##
# Temperature in celsius calculation notes:
# T = C0 + C1*RTC + C2*RTC^2 + ZT
# RTC = ((RPT*ADC/ADCmax)/(1-ADC/ADCmax)) - DTL*KT
# Where:
# T, Temperature
# C0 = -245.653
# C1 = 0.235482
# C2 = 0.000010171
# DTL, Distance from sensor "zero" to temperature element
# KT, Resistance of copper wire (0.63 Ohm/m)
# ZT, Zero Level (offset adjustment)
# RPT, Value of pull up resistor (Probably 4.02K)
# ADC, Current value of ADC (read DB value for that)
# ADCmax, Max value of ADC => 0xFFFFFF = 16777215
TEMP_RST = {
    'name': 'Temperature Resistance',
    'formula': '(rpt*self)/(adc_max-self) - dtl*0.63',
    'min_alarm': 800,
    'min_alarm_message': SHORT_CIRCUIT,
    'max_alarm': 1600,
    'max_alarm_message': OPEN_CIRCUIT
}
CELSIUS = {
    'name': 'celsius',
    'formula': '-245.653 + 0.235482*temperature_resistance + 0.000010171*temperature_resistance**2 + zt',
    'measuring_units': u'°C',
    'min_value': -40,
    'max_value': 80,
    'str_format': '{0:.1f}'
}


## Headers Instance ##
HEADERS = {
    'headers': (
        {
            'name': 'Temperature',
            'groups': {
                'constants': [DTL, ZT, RPT],
                'variables': [TEMP_RST],
                'unit_list': [CELSIUS, FAHRENHEIT]
            }
        },
    )
}
