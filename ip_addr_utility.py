#!/usr/bin/python
"""
Script Responsible for changing IP Address of the system
"""

### INCLUDES ###
import os
import sys
import logging

from py_knife import platforms

from gate.conversions import get_net_addresses, get_ip_scheme, validate_ip_address
from gate.system import SystemSettings


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def clear_screen():
    # print chr(27) + "[2J"
    os.system('clear')


def get_user_input():
    return raw_input('Your Selection: ').lower()


### CLASSES ###
class IPUtility(object):
    def __init__(self):
        self._settings = SystemSettings()
        self._running = True
        self._invalid_address = False

    def print_user_interface(self):
        ip_address, net_mask = get_net_addresses()
        ip_scheme = get_ip_scheme()
        print '*** IP ADDRESSING UTILITY ***'
        print 'Current IP Address:{0:>18}'.format(str(ip_address))
        print 'Current IP NetMask:{0:>18}'.format(str(net_mask))
        print 'Current IP Scheme: {0:>18}'.format(ip_scheme)
        print '\nYour Options:'
        print '1. Type new IP Address and Net Mask(optional), e.g.: 169.254.141.111 (255.255.0.0)'
        print '2. Set dynamic IP Addressing, e.g.: dynamic'
        print '3. Refresh this screen by pressing enter'
        print '4. Exit Utility, e.g.: exit'
        if self._invalid_address:
            print 'ERROR: Invalid IP Address! Try again!\n'
        else:
            print '\n'

    def process_input(self, user_input):
        self._invalid_address = False

        _user_input_list = user_input.split(' ')
        _ip_address = _user_input_list[0]

        if len(_user_input_list) >= 2:
            _net_mask = _user_input_list[1]
        else:
            _net_mask = '255.255.255.0'

        # LOGGER.debug("_ip_address = " + _ip_address)
        # LOGGER.debug("_net_mask = " + _net_mask)
        # LOGGER.debug("len(_user_input_list) = " + str(len(_user_input_list)))

        valid_ip_address = validate_ip_address(_ip_address) and validate_ip_address(_net_mask)

        if len(_ip_address.split('.')) == 4:
            self._invalid_address = not valid_ip_address

        if valid_ip_address:
            self._settings.change_network_settings('static', _ip_address, _net_mask)
        elif user_input in ('2', 'dynamic', 'd'):
            self._settings.change_network_settings('dynamic')
        elif user_input in ('4', 'exit', 'e'):
            self._running = False

    def run(self):
        clear_screen()
        while self._running:
            self.print_user_interface()
            user_input = get_user_input()
            self.process_input(user_input)
            clear_screen()


if __name__ == '__main__':
    if platforms.PLATFORM == platforms.SYNAPSE_E10:
        ip_utility = IPUtility()
        ip_utility.run()

    else:
        sys.exit('IP Addressing utility works only on Synapse E10 platform at the moment!')
