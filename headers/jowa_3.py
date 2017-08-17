"""
Jowa Header, Code # 3
Battery Voltage
"""

### INCLUDES ###
from common import JOWA_BATT_THRESHOLD, LOW_BATTERY


### CONSTANTS ###
## Battery Voltage Units and Variables ##
# Battery voltage calculation notes:
# Vbat = ((R5+R4)/R5)*Vch3 = (2*R/R)*Vch3 =
#   2*Vch3 = 2*(ADC/ADCmax)*Vref
# Where:
# Vref, ADC Voltage Reference (Currently 2.5V)
# ADC, Current value of ADC (read DB value for that)
# ADCmax, Max value of ADC => 0xFFFFFF = 16777215
VOLTAGE = {
    'name': 'voltage',
    'formula': '2*adc_ref*(self/adc_max)',
    'measuring_units': 'V',
    'min_value': 0,
    'max_value': 5,
    'min_alarm': JOWA_BATT_THRESHOLD,
    'min_alarm_message': LOW_BATTERY,
}

## Headers Instance ##
HEADERS = [
    {
        'name': 'Battery',
        'groups': {
            'unit_list': [VOLTAGE]
        },
        'diagnostics': True
    }
]
