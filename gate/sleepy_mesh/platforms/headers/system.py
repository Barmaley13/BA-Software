# -*- coding: utf-8 -*-
"""
System Headers
"""

### INCLUDES ###
import copy

from common import PERCENT, MILLISECONDS, LIFE_TIME


### CONSTANTS ###
## Strings ##
LONG_WAKE = ' is too long!'

## System Diagnostics Units ##
WAKE_MILLISECONDS = copy.deepcopy(MILLISECONDS)
WAKE_MILLISECONDS.update({
    'max_alarm': 500,
    'max_alarm_message': LONG_WAKE
})

## System Diagnostics Headers ##
RECENT_SYNC_RATE = {
    'name': 'Recent Sync Rate',
    'data_field': 'recent_sync_rate',
    'groups': {'unit_list': [PERCENT]}
}

LIFE_SYNC_RATE = {
    'name': 'Life Sync Rate',
    'data_field': 'life_sync_rate',
    'groups': {'unit_list': [PERCENT]}
}

SYNC_CURRENT = {
    'name': 'Current Wake Time',
    'data_field': 'sync_current',
    'groups': {'unit_list': [WAKE_MILLISECONDS]}
}

SYNC_AVERAGE = {
    'name': 'Average Wake Time',
    'data_field': 'sync_average',
    'groups': {'unit_list': [MILLISECONDS]}
}

DELAY_CURRENT = {
    'name': 'Current Sync Delay',
    'data_field': 'delay_current',
    'groups': {'unit_list': [MILLISECONDS]}
}

DELAY_AVERAGE = {
    'name': 'Average Sync Delay',
    'data_field': 'delay_average',
    'groups': {'unit_list': [MILLISECONDS]}
}


## Headers Instance ##
HEADERS = {
    'platform': 'system',
    'display_headers': (),
    'diagnostics_headers': (
        LIFE_TIME,
        RECENT_SYNC_RATE,
        LIFE_SYNC_RATE,
        SYNC_CURRENT,
        SYNC_AVERAGE,
        DELAY_CURRENT,
        DELAY_AVERAGE
    )
}
