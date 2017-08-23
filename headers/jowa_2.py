# -*- coding: utf-8 -*-
"""
Jowa Header, Code # 2
Volume
"""


### CONSTANTS ###
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

## Volume Units and Variables ##
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
HEADER = {
    'name': 'Volume',
    'groups': {
        'constants': [TANK_TYPE, AREA, DIAMETER, LENGTH],
        'variables': [LITERS_MAX, KILO_LITERS_MAX, GALLONS_MAX, KILO_GALLONS_MAX],
        'unit_list': [LITERS, KILO_LITERS, GALLONS, KILO_GALLONS]
    }
}
