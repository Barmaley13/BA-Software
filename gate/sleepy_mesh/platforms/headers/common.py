# -*- coding: utf-8 -*-
"""
Common Constants used across different headers (as well as headers that belong to different platforms)
"""

### INCLUDES ###
import copy
import logging

from gate.conversions import time_str


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)

## Global Alarms ##
JOWA_BATT_THRESHOLD = 3.25
SWE_BATT_THRESHOLD = 2.5                # Introduced for debugging purposes
SYNC_THRESHOLD = 80

## Global Alarm Messages ##
LOW_BATTERY = " voltage is low!"
LOW_SYNC = " is low!"

## Platform Specific Constants ##
JOWA_ADC_REF = 2.5                      # Volts
JOWA_ADC_MAX = float(0xFFFFFF)          # 24-bit ADC
SWE_ADC_MAX = float(0x3FF)              # 12-bit ADC

## Platform Specific Header Constants ##
JOWA_MAX = {
    'name': 'adc_max',
    'default_value': JOWA_ADC_MAX
}

JOWA_REF = {
    'name': 'adc_ref',
    'default_value': JOWA_ADC_REF
}

SWE_MAX = {
    'name': 'adc_max',
    'default_value': SWE_ADC_MAX
}

## Global Header Constants, Variables and Units ##
FLOATING_SWITCH = {
    'name': 'floating_switch',
    'formula': '1-round(self/adc_max)',         # Opposite polarity
    'measuring_units': 'on/off',
    'min_value': 0,
    'max_value': 1.0,
    'min_alarm': 0.5,
    'max_alarm': 0.5,
}

# Percent Units #
PERCENT = {
    'name': 'percent',
    'formula': 'self',
    'measuring_units': '%',
    'min_value': 0,
    'max_value': 100,
    'str_format': '{0:.0f}'
}

_RSR_PERCENT = copy.deepcopy(PERCENT)
_RSR_PERCENT.update({
    'formula': 'int(100*(sum(recent_syncs))/float(len(recent_syncs)))',
    'min_alarm': SYNC_THRESHOLD,
    'min_alarm_message': LOW_SYNC
})

_LSR_PERCENT = copy.deepcopy(PERCENT)
_LSR_PERCENT.update({
    'formula': 'int(100*(successful_syncs)/float(total_syncs))'
})

_DRAW_PERCENT = copy.deepcopy(PERCENT)
_DRAW_PERCENT.update({
    'formula': '(1 - self)*100'
})

# Temperature Units #
MCU_CELSIUS = {
    'name': 'celsius',
    'formula': 'self',
    'measuring_units': u'°C',
    'min_value': -40,
    'max_value': 80
}
FAHRENHEIT = {
    'name': 'fahrenheit',
    'formula': '(celsius*9)/5 + 32',
    'measuring_units': u'°F',
    'min_value': -40,
    'max_value': 180,
    'str_format': '{0:.1f}'
}

# Voltage Units #
BM_VOLTAGE = {
    'name': 'voltage',
    'formula': 'self',
    'measuring_units': 'V',
    'min_value': 1.5,
    'max_value': 4,
    'min_alarm': SWE_BATT_THRESHOLD,
    'min_alarm_message': LOW_BATTERY
}

# Time Units #
MILLISECONDS = {
    'name': 'milliseconds',
    'formula': 'self*1000',
    'measuring_units': 'ms'
}

SECONDS = {
    'name': 'seconds',
    'formula': 'self',
    'measuring_units': 'seconds'
}

_DRAW_SECONDS = copy.deepcopy(SECONDS)
_DRAW_SECONDS.update({
    'formula': 'life_time * (1 - self) / self',
})

MINUTES = {
    'name': 'minutes',
    'formula': 'seconds / 60',
    'measuring_units': 'minutes'
}

HOURS = {
    'name': 'hours',
    'formula': 'minutes / 60',
    'measuring_units': 'hours'
}

DAYS = {
    'name': 'days',
    'formula': 'hours / 24',
    'measuring_units': 'days'
}

MONTHS = {
    'name': 'months',
    'formula': 'days / 30',
    'measuring_units': 'months'
}

YEARS = {
    'name': 'years',
    'formula': 'months / 12',
    'measuring_units': 'years'
}

COMPOSITE_TIME = {
    'name': 'composite_time',
    'formula': 'self',
    'measuring_units': 'yy-mm-dd hh:mm:ss',
    'str_format': time_str
}

_DRAW_COMPOSITE_TIME = copy.deepcopy(COMPOSITE_TIME)
_DRAW_COMPOSITE_TIME.update({
    'formula': 'seconds',
})

## Header Instances ##
# Diagnostic Constants #
_RSR_RECENT_SYNCS = {
    'name': 'recent_syncs',
    'default_value': []
}

_LSR_SUCCESSFUL_SYNCS = {
    'name': 'successful_syncs',
    'default_value': 0
}

_LSR_TOTAL_SYNCS = {
    'name': 'total_syncs',
    'default_value': 0
}

_DRAW_LIFE_TIME = {
    'name': 'life_time',
    'default_value': None
}

# Global Diagnostics Headers #
LIFE_TIME = {
    'name': 'Life Time',
    'data_field': 'life_time',
    'groups': {'unit_list': [SECONDS, MINUTES, HOURS, DAYS, MONTHS, YEARS, COMPOSITE_TIME]}
}

RECENT_SYNC_RATE = {
    'name': 'Recent Sync Rate',
    'data_field': 'recent_sync_rate',
    'groups': {
        'constants': [_RSR_RECENT_SYNCS],
        'unit_list': [_RSR_PERCENT]
    }
}

LIFE_SYNC_RATE = {
    'name': 'Life Sync Rate',
    'data_field': 'life_sync_rate',
    'groups': {
        'constants': [_LSR_SUCCESSFUL_SYNCS, _LSR_TOTAL_SYNCS],
        'unit_list': [_LSR_PERCENT]
    }
}

TOTAL_DRAW = {
    'name': 'Estimated Battery',
    'data_field': 'total_draw',
    'groups': {
        'constants': [_DRAW_LIFE_TIME],
        'unit_list': [_DRAW_PERCENT, _DRAW_SECONDS, MINUTES, HOURS, DAYS, MONTHS, YEARS, _DRAW_COMPOSITE_TIME]}
}

# Platform Specific Diagnostics Headers #
# Note: It is actually Link Quality but Per requested to rename to Signal Strength
JOWA_LQ = {
    'name': 'Signal Strength',
    'data_field': 'lq',
    'groups': {'unit_list': [PERCENT]}
}

SWE_BATT = {
    'name': 'Battery',
    'data_field': 'batt',
    'groups': {'unit_list': [BM_VOLTAGE]}
}
SWE_LQ = {
    'name': 'Link Quality',
    'data_field': 'lq',
    'groups': {'unit_list': [PERCENT]}
}

MCU_TEMP = {
    'name': 'MCU Temperature',
    'data_field': 'temp',
    'groups': {'unit_list': [MCU_CELSIUS, FAHRENHEIT]}
}

## Platform Specific Dynamic Imports ##
JOWA_CONSTANTS = (JOWA_MAX, JOWA_REF)
SWE_CONSTANTS = (SWE_MAX, )

DISPLAY_HEADERS = ()
JOWA_DISPLAY_HEADERS = (JOWA_LQ, MCU_TEMP)
SWE_DISPLAY_HEADERS = (SWE_BATT, SWE_LQ, MCU_TEMP)

DIAGNOSTIC_HEADERS = (LIFE_TIME, RECENT_SYNC_RATE, LIFE_SYNC_RATE, TOTAL_DRAW)
JOWA_DIAGNOSTIC_HEADERS = ()
SWE_DIAGNOSTIC_HEADERS = ()
