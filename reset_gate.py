#!/usr/bin/python
"""
Script that resets the gate.
For more detailed information refer to documentation under ~/gate_data/docs
"""

### INCLUDES ###
import time

from gate.main import reset_aes_settings
from gate.leds import off, green, red, yellow, button
from gate.system import SYSTEM_DEFAULTS
from gate.configure import configure_system, clean_system


### CONSTANTS ###
PULSE_DURATION = 0.25       # seconds


### MAIN ###
if __name__ == '__main__':
    # Do fancy LED flashing while button is pressed
    while button():
        for color in (green, red, yellow):
            color()
            time.sleep(PULSE_DURATION)
            off()
            time.sleep(PULSE_DURATION)

    # Reset everything after button has been released and start the gate
    def _aes_reset_complete_callback():
        """ Finishing reset procedures """
        clean_system()

        configure_options = {
            'interactive': False,
            'update_os': False,
            'install_pip_packages': False,
            'change_hostname': 'gate',
            'configure_ip_utility': False,
            'update_network': SYSTEM_DEFAULTS,
            'install_ftp': False,
            'configure_auto_start': False,
            'start_gate': True
        }
        configure_system(configure_options)

    reset_aes_settings(reset_complete_callback=_aes_reset_complete_callback)
