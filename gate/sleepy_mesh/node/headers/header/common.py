"""
Some common constants for this package
"""


### CONSTANTS ###
## Default Data Fields ##
ADC_FIELDS = ('adc0', 'adc1', 'adc2', 'adc3', 'adc4', 'adc5', 'adc6', 'adc7')
DEFAULT_FIELDS = ('lq', 'temp', 'batt')
DISPLAY_FIELDS = ADC_FIELDS + DEFAULT_FIELDS
DIAGNOSTIC_FIELDS = ('life_time', 'recent_sync_rate', 'life_sync_rate', 'total_draw')
ALL_FIELDS = DISPLAY_FIELDS + DIAGNOSTIC_FIELDS

## Strings ##
MIN_ALARM = ' Min Alarm has been triggered!'
MAX_ALARM = ' Max Alarm has been triggered!'
