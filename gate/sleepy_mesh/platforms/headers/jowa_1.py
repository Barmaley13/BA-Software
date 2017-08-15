# -*- coding: utf-8 -*-
"""
Jowa Header, Code # 1
Level/Volume Pair
"""

### IMPORTS ###
from common import SHORT_CIRCUIT, OPEN_CIRCUIT


### CONSTANTS ###
## Level Constants ##
TH = {
    'name': 'TH',
    'default_value': 20.0,
    'measuring_units': 'meters',
    'description': 'Tank Height',
    'min_value': 0.5,
    'max_value': 20,
    'step': 0.001
}
DTB = {
    'name': 'DTB',
    'default_value': 20.1,
    'measuring_units': 'meters',
    'description': 'Distance to Tank Bottom',
    'min_value': 0.5,
    'max_value': 20.5,
    'step': 0.001
}
N = {
    'name': 'N',
    'default_value': [0.000, 0.044],
    'default_selected': 1,
    'measuring_units': 'meters',
    'description': 'Nipple height of sensor housing',
    'min_value': 0,
    'max_value': 100,
    'step': 0.01
}
DTH = {
    'name': 'DTH',
    'default_value': [0.088, 0.220],
    'measuring_units': 'meters',
    'description': 'Distance to Top Helix'
}
AD = {
    'name': 'AD',
    'default_value': 0.125,
    'measuring_units': 'meters',
    'description': 'Actuation Depth of sensor',
    'min_value': 0.1,
    'max_value': 0.25,
    'step': 0.001
}
SG = {
    'name': 'SG',
    'default_value': 1,
    'measuring_units': 'g/cc',
    'description': 'Specific Gravity of liquid being gauged',
    'min_value': 0.4,
    'max_value': 2,
    'step': 0.001
}
ZL = {
    'name': 'ZL',
    'default_value': 0.0,
    'measuring_units': 'meters',
    'description': 'Zero Level (offset adjustment)',
    'min_value': -0.5,
    'max_value': 0.5,
    'step': 0.001
}
RS = {
    'name': 'RS',
    'default_value': 20000,
    'measuring_units': 'ohms',
    'description': 'Resistance of Sensor',
    'min_value': 300,
    'max_value': 50000,
    'step': 1
}
RG = {
    'name': 'RG',
    'default_value': 1000,
    'measuring_units': 'ohms/meter',
    'description': 'Resistance Gradient of sensor',
    'min_value': 950,
    'max_value': 1050,
    'step': 0.01
}
# External RPL
# RPL = {
#     'name': 'RPL',
#     'default_value': 15000,
#     'measuring_units': 'ohms',
#     'description': 'Value of level pull up resistor',
#     'min_value': 500,
#     'max_value': 1000000,
#     'step': 1
# }
# Internal RPL
RPL = {
    'name': 'RPL',
    'default_value': 15000
}


## Volume Constants ##
TANK_TYPE = {
    'name': 'Tank Type',
    'default_value': ['Constant', 'Vertical', 'Horizontal'],
    'measuring_units': '',
    'description': ['Constant Area Tank', 'Vertical Cylindrical Tank', 'Horizontal Cylindrical Tank']
}
AREA = {
    'name': 'Area',
    'default_value': None,
    'measuring_units': u'meters²',
    'description': 'Specify Area',
    'min_value': 0.01,
    'max_value': 500,
    'step': 0.01
}
DIAMETER = {
    'name': 'Diameter',
    'default_value': None,
    'measuring_units': 'meters',
    'description': 'Specify Diameter',
    'min_value': 0.01,
    'max_value': 100,
    'step': 0.01
}
LENGTH = {
    'name': 'Length',
    'default_value': None,
    'measuring_units': 'meters',
    'description': 'Specify Length',
    'min_value': 0.01,
    'max_value': 30,
    'step': 0.01
}

## Level Units and Variables ##
# Liquid Level in meters calculation notes:
# L = K1 + RL*K2
# K1 = DTB + N - DTH + AD/SG +ZL
# K2 = -1/RG
# RL = (RPL*ADC/ADCmax)/(1-ADC/ADCmax)
# Where:
# L, Liquid Level
# DTB, Distance to Tank Bottom
# N, Nipple height of sensor housing
# DTH, Distance to Top Helix
# AD, Actuation Depth of sensor
# SG, Specific Gravity of liquid being gauged
# ZL, Zero Level (offset adjustment)
# RG, Resistance Gradient of sensor
# RPL, Value of pull up resistor (Probably 15.0K)
# ADC, Current value of ADC (read DB value for that)
# ADCmax, Max value of ADC => 0xFFFFFF = 16777215
LEVEL_K1 = {
    'name': 'level_k1',
    'formula': 'dtb+n-dth+ad/sg+zl'
}
LEVEL_K2 = {
    'name': 'level_k2',
    'formula': '-1/rg'
}
LEVEL_RST = {
    'name': 'Level Resistance',
    'formula': '(rpl*self/adc_max)/(1-self/adc_max)',
    'min_alarm': 25,
    'min_alarm_message': SHORT_CIRCUIT,
    'max_alarm': 20000,
    'max_alarm_message': OPEN_CIRCUIT
}
_METERS = {
    'name': '_meters',
    'formula': 'level_k1 + level_resistance*level_k2'
}
TH_FEET = {
    'name': 'th_feet',
    'formula': 'th*3.28084'
}
LITERS_MAX = {
    'name': 'liters_max',
    'formula': '_get_liters(constants, th)'
}
KILO_LITERS_MAX = {
    'name': 'kilo_liters_max',
    'formula': 'liters_max/1000'
}
GALLONS_MAX = {
    'name': 'gallons_max',
    'formula': 'liters_max * 0.264172'
}
KILO_GALLONS_MAX = {
    'name': 'kilo_gallons_max',
    'formula': 'gallons_max/1000'
}

LEVEL_PERCENT = {
    'name': 'percent',
    'formula': '_meters*100/th',
    'measuring_units': '%',
    'min_value': 0,
    'max_value': 100
}
METERS = {
    'name': 'meters',
    'formula': '_meters',
    'measuring_units': 'meters',
    'min_value': 0,
    'max_value': 'th'
}
FEET = {
    'name': 'feet',
    'formula': 'meters*3.28084',
    'measuring_units': 'feet',
    'min_value': 0,
    'max_value': 'th_feet'
}
LITERS = {
    'name': 'liters',
    'formula': '_get_liters(constants, meters)',
    'measuring_units': 'liters',
    'min_value': 0,
    'max_value': 'liters_max',
    'str_format': '{0:.0f}'
}
KILO_LITERS = {
    'name': 'kilo_liters',
    'formula': 'liters/1000',
    'measuring_units': u'KLiters (m³)',
    'min_value': 0,
    'max_value': 'kilo_liters_max',
    'str_format': '{0:.0f}'
}
GALLONS = {
    'name': 'gallons',
    'formula': 'liters * 0.264172',
    'measuring_units': 'gallons',
    'min_value': 0,
    'max_value': 'gallons_max',
    'str_format': '{0:.0f}'
}
KILO_GALLONS = {
    'name': 'kilo_gallons',
    'formula': 'gallons/1000',
    'measuring_units': 'KGallons',
    'min_value': 0,
    'max_value': 'kilo_gallons_max',
    'str_format': '{0:.0f}'
}

## Headers Instance ##
HEADERS = [
    {
        'name': 'Level',
        'groups': {
            'constants': [TH, DTB, N, DTH, AD, SG, ZL, RS, RG, RPL],
            'variables': [LEVEL_K1, LEVEL_K2, LEVEL_RST, _METERS, TH_FEET],
            'unit_list': [LEVEL_PERCENT, METERS, FEET]
        },
        'live_cookie': {'units': 0, 'table_units': [1]},
        'log_cookie': {'units': 1, 'table_units': [1]},
    },
    {
        'name': 'Volume',
        'groups': {
            'constants': [TANK_TYPE, AREA, DIAMETER, LENGTH],
            'variables': [LITERS_MAX, KILO_LITERS_MAX, GALLONS_MAX, KILO_GALLONS_MAX],
            'unit_list': [LITERS, KILO_LITERS, GALLONS, KILO_GALLONS]
        }
    }
]
