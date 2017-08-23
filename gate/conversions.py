"""
Unit Conversion Functions
"""

### INCLUDES ###
import os
import subprocess
import socket
import re
import binascii
import math
import commands
import logging

from py_knife import platforms


### CONSTANTS ###
## RTC Related ##
# RTC timer (integer) runs of of 4 second clock, where 0x7FFF is max
INT_DIVIDER = 4
# RTC timer (remainder) runs of of 1/64 Hz clock, where 0x00FF is max
REMAINDER_MULTIPLIER = 64

BASE_COUNTER_PRECISION = 64
CYCLES_MAX_INT = 0x7FFF

## Internal Name ##
ALLOWED_CHARS = re.compile('[a-z0-9\-_:.]')
VERSION_CHARS = re.compile('[0-9.]')

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
## Raw Data Related ##    
def bin_to_hex(bin_val):
    """ Converts binary to HEX string """
    return binascii.b2a_hex(bin_val).upper()


def hex_to_bin(hex_val):
    """ Converts HEX string to binary """
    return binascii.a2b_hex(hex_val)


def bin_to_int(bin_val):
    """ Converts binary to HEX string """
    try:
        output = int(bin_to_hex(bin_val), 16)

    except:
        output = None

    return output


## Rounding ##
def round_int(number, rounding, power):
    """ Rounds up int to using specified power """
    output = None

    if number is not None:
        rounding1 = rounding2 = None

        if rounding == 'ceil':
            rounding1 = math.ceil
            rounding2 = math.floor
        elif rounding == 'floor':
            rounding1 = math.floor
            rounding2 = math.ceil

        precision = 10 ** power

        if number >= 0:
            output = int(rounding1(number / precision)) * precision
        else:
            output = int(rounding2(number / precision)) * precision

    return output


## String related ##
def internal_name(input_name):
    """ Generates internal name """
    if type(input_name) not in (str, unicode):
        input_name = str(input_name)

    _internal_name = input_name.replace(' ', '_').lower()
    output = ''.join(ALLOWED_CHARS.findall(_internal_name))
    return output


def external_name(input_name):
    """ Generates external name """
    _external_name = input_name.replace('_', ' ').split()
    _external_name = map(str.capitalize, _external_name)
    output = ' '.join(_external_name)
    return output


def find_version(software_name):
    """ Finds version and strips everything else """
    output = ''.join(VERSION_CHARS.findall(software_name))
    return output


def time_str(input_seconds):
    """ Converts seconds to 'YY-MM-DD HH:MM:SS' format """
    output = None

    if input_seconds is not None:
        total_seconds = int(input_seconds)
        seconds = total_seconds % 60
        total_minutes = total_seconds / 60
        minutes = total_minutes % 60
        total_hours = total_minutes / 60
        hours = total_hours % 24
        total_days = total_hours / 24
        days = total_days % 30
        total_months = total_days / 30
        months = total_months % 12
        years = total_months / 12
        output = "{0:0>2}-{1:0>2}-{2:0>2} {3:0>2}:{4:0>2}:{5:0>2}".format(years, months, days, hours, minutes, seconds)

    return output


## Misc ##
def getstatusoutput(cmd):
    """
    Return (status, output) of executing cmd in a shell.
    This new implementation should work on all platforms.
    """
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    output = "".join(pipe.stdout.readlines())
    sts = pipe.returncode
    if sts is None:
        sts = 0

    return sts, output


## IP Addressing Helpers ##
# FIXME: Make sure this works on Raspberry Pi!
def online_status():
    """ Test if we are currently online """
    _online_status = True

    if platforms.PLATFORM in platforms.EMBEDDED_PLATFORMS:
        _online_status = False
        if ethernet_plugged_in():
            ip_address, net_mask = get_net_addresses()

            address_acquired = bool(ip_address is not None)

            if address_acquired:
                ping_output = commands.getoutput('ping google.com -c 1 -W 1').split('\n')
                # 'ping google.com -n 1 -w 1'       # Windows

                if len(ping_output) > 4:
                    statistics_line = ping_output[4].split(',')
                    if len(statistics_line) > 2:
                        packet_loss = statistics_line[2].split()[0]
                        if '%' in packet_loss:
                            packet_loss_rate = int(packet_loss.split('%')[0])
                            _online_status = bool(packet_loss_rate < 100)

    return _online_status


def ethernet_plugged_in():
    """ Check if ethernet is plugged in. Return True or False """
    cable_plugged = False
    if platforms.PLATFORM in platforms.EMBEDDED_PLATFORMS:
        network_state = open('/sys/class/net/eth0/operstate', 'r')
        cable_plugged = bool('up' in network_state.read())
        network_state.close()

    return cable_plugged


# FIXME: Make sure this works on Raspberry Pi!
def get_ip_scheme():
    """ Fetch current ip addressing scheme from a file """
    ip_scheme = 'dynamic'

    if platforms.PLATFORM in platforms.EMBEDDED_PLATFORMS:
        if platforms.PLATFORM == platforms.RASPBERRY_PI:
            import configure.configure_pi as configure_module

        else:
            import configure.configure_e10 as configure_module

        ip_file_path = getattr(configure_module, 'NETWORK_SETTINGS_FILE')
        if os.path.isfile(ip_file_path):
            if platforms.PLATFORM == platforms.SYNAPSE_E10:
                ip_file = open(ip_file_path, 'r')
                if '/sbin/udhcpc -b' not in ip_file.read():
                    ip_scheme = 'static'
                ip_file.close()

            if platforms.PLATFORM == platforms.RASPBERRY_PI:
                with open(ip_file_path) as network_file:
                    network_lines = network_file.readlines()

                for network_line in network_lines:
                    ip_scheme_match = re.match('^\s*static[ ]+(ip_address|ip6_address)=', network_line, re.I)
                    if ip_scheme_match is not None:
                        ip_scheme = 'static'

    return ip_scheme


def get_net_addresses():
    """ Extracts ip address using ifconfig command """
    ip_address = None
    subnet_mask = None

    command = 'ifconfig'
    if platforms.PLATFORM == platforms.WINDOWS:
        command = 'ipconfig'

    status, ipconfig_output = getstatusoutput(command)

    if ipconfig_output is not None:
        if platforms.PLATFORM == platforms.WINDOWS:
            regex_pattern = '.*?Address.*?: (' + '[\.]'.join(['\d{1,3}'] * 4) + ').*?\n'
            regex_pattern += '.*?Mask.*?: (' + '[\.]'.join(['\d{1,3}'] * 4) + ')'
        else:
            # TODO: Test this works properly on MAC (and other non windows systems)
            regex_pattern = '.*?addr:(' + '[\.]'.join(['\d{1,3}'] * 4) + ')'
            regex_pattern += '.*?Mask:(' + '[\.]'.join(['\d{1,3}'] * 4) + ')'

        if regex_pattern is not None:
            # LOGGER.debug(regex_pattern)
            net_addresses = re.findall(regex_pattern, ipconfig_output)
            if platforms.PLATFORM != platforms.WINDOWS:
                lo_pair = ('127.0.0.1', '255.0.0.0')
                if lo_pair in net_addresses:
                    net_addresses.remove(lo_pair)

            if len(net_addresses):
                ip_address, subnet_mask = net_addresses[0]

    else:
        # Note: Does not work with multiple network cards!
        ip_address = socket.gethostbyname(socket.gethostname())
        subnet_mask = '255.255.255.0'

    return ip_address, subnet_mask


def validate_ip_address(ip_address):
    """ Validates IP Address """
    valid_ip_address = False
    ip_address = ip_address.split('.')
    if len(ip_address) == 4:
        valid_ip_address = True
        for ip_digit in ip_address:
            try:
                ip_digit = int(ip_digit)
                valid_ip_address &= bool(0 <= ip_digit <= 255)
            except:
                valid_ip_address = False

    return valid_ip_address


def validate_oid(oid_address):
    """ Validates SNMP OID Address """
    valid_oid = True
    try:
        for oid_digit in oid_address.split('.'):
            valid_oid &= oid_digit.isdigit()

        for oid_index in (0, -1):
            valid_oid &= oid_address[oid_index] != '.'

    except:
        valid_oid = False

    return valid_oid


## Integer, Remainder Conversions ##
# Node Conversions (RTC Conversions) #
def get_int_rem(float_value):
    """ Combined integer and remainder (for node) """
    return _get_integer(float_value), _get_remainder(float_value)


def get_float(int_value, remainder_value):
    """ Convert integer and remainder portions(ints) to float """
    output = float(int_value) * INT_DIVIDER + float(remainder_value) / REMAINDER_MULTIPLIER
    LOGGER.debug('get_float: ' + str(output))
    return output


def round_float(float_value):
    """
    Converts float value to integer and remainder
    Combines those back to float
    """
    args = get_int_rem(float_value)
    output = get_float(*args)
    return output


# Base Conversions (internal ms counter Conversions) #
def get_base_int_rem(float_value):
    """ Converts float value to integer and remainder (for base node) """
    integer = int(float_value * 1000 / BASE_COUNTER_PRECISION) & CYCLES_MAX_INT
    remainder = 0           # this value is ignored by base

    return integer, remainder


def get_base_float(int_value, remainder_value=None):
    """ Convert integer and remainder portions(ints) to float """
    output = float(int_value) * BASE_COUNTER_PRECISION / 1000
    LOGGER.debug('get_base_float: ' + str(output))
    return output


def round_base_float(float_value):
    """
    Converts float value to integer and remainder
    Combines those back to float
    """
    args = get_base_int_rem(float_value)
    output = get_base_float(*args)
    return output


# Battery Life #
def get_battery_life(network):
    """ Returns battery life in years """
    # Battery Life(hours) = Battery Capacity/Average Current
    # Hours Per Year = 24 hours/day * 30 days/month * 12 months/year
    # Battery Life(years) = Battery Life(hours)/(Hours Per Year)
    # Average Current = (Awake Current * Awake Period + 
    # + Asleep Current * Asleep Period)/(Awake Period + Asleep Period)
    capacity = network['battery']['capacity']
    wake_period = network['wake']
    sleep_period = network['sleep']
    wake_current = network['battery']['awake_current']
    sleep_current = network['battery']['asleep_current']
    battery_life = (capacity * (wake_period + sleep_period)) / (
        24 * 30 * 12 * (wake_current * wake_period + sleep_current * 0.000001 * sleep_period))
    battery_life = "{0:.2f}".format(battery_life)
    return battery_life


## Misc Helpers ##
def fetch_item(item_dict, item_index):
    """
    :param item_dict: dictionary used for item fetch
    :param item_index: either item key or item index
    :return: Returns item
    """
    output = None

    item_type = type(item_index)
    if item_type is int:
        if item_index < len(item_dict):
            output = item_dict.values()[item_index]
        else:
            LOGGER.error("No such unit index '{}' during 'fetch_item' execution!".format(item_index))

    elif item_type in (str, unicode):
        unit_key = item_index.encode('ascii', 'ignore')
        if unit_key in item_dict.keys():
            output = item_dict[unit_key]
        else:
            LOGGER.error("No such unit key '{}' during 'fetch_item' execution!".format(unit_key))

    else:
        LOGGER.error("Wrong item type: '{}' during 'fetch_item' execution!".format(item_type))

    return output


## Private Function ##
def _get_integer(float_value):
    """ Extracts integer portion(int) from float """
    output = int(float_value) / INT_DIVIDER
    LOGGER.debug('_get_integer: ' + str(output))
    return output


def _get_remainder(float_value):
    """ Extracts remainder portion(int) from float """
    output = int((float(float_value) % INT_DIVIDER) * REMAINDER_MULTIPLIER)
    LOGGER.debug('_get_remainder: ' + str(output))
    return output


### DYNAMIC CONSTANTS ###
TIMEOUT_MAX_FLOAT = get_float(0x7FFF, 0x00FF)
