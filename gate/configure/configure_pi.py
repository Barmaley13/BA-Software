"""
Configure Raspberry Pi Script
Project: `Bolder Automation <http://bolderautomation.net>`_
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""


### INCLUDES ###
import os
import re
import subprocess
import logging

from optparse import OptionParser

from distutils.spawn import find_executable

from py_knife import file_system
from py_knife.ordered_dict import OrderedDict

import common
from common import install_pip_packages, change_hostname


### CONSTANTS ###
## Default Pi Settings ##
DEFAULT_USER = 'pi'
DEFAULT_HOSTNAME = 'raspberrypi'
DEFAULT_PASSWORD = 'raspberry'

## apt_get Settings ##
APT_GET_PACKAGES = ['vi', 'vim', 'emacs', 'nano', 'minicom', 'dos2unix']
APT_GET_PACKAGES_STR = ', '.join(APT_GET_PACKAGES)

## VNC Settings ##
VNC_SETTINGS = '-geometry 1920x1200 -depth 24 -dpi 96'
VNC_CURSOR_SETTINGS = '-cursor_name left_ptr'

## OS Files/Folders ##
DEFAULT_HOME_FOLDER = os.path.join(common.FILE_SYSTEM_ROOT, 'home', DEFAULT_USER)
FTP_SETTINGS_FILE = os.path.join(common.ETC_FOLDER, 'pureftpd.passwd')
SAMBA_SETTINGS_FILE = os.path.join(common.ETC_FOLDER, 'samba', 'smb.conf')
XSTARTUP_FILE = os.path.join(DEFAULT_HOME_FOLDER, '.vnc', 'xstartup')
VNCBOOT_FILE = os.path.join(common.INITD_FOLDER, 'vncboot')
AUTO_START_FILE = os.path.join(common.INITD_FOLDER, 'gate')
NETWORK_INTERFACES_FILE = os.path.join(common.ETC_FOLDER, 'network', 'interfaces')
NETWORK_SETTINGS_FILE = os.path.join(common.ETC_FOLDER, 'dhcpcd.conf')
BOOT_FOLDER = os.path.join(common.FILE_SYSTEM_ROOT, 'boot')
RPI3_CONFIG_FILE = os.path.join(BOOT_FOLDER, 'config.txt')
RPI3_CMDLINE_FILE = os.path.join(BOOT_FOLDER, 'cmdline.txt')

## Template Paths ##
AUTO_START_TEMPLATE_FILE = os.path.join(common.INITD_TEMPLATE_FOLDER, 'gate')

## Globals ##
password = DEFAULT_PASSWORD

## Option Parser ##
OPTION_PARSER = OptionParser()
OPTION_PARSER.add_option('-d', '--disable_interactive', dest='interactive', action='store_false', default=True,
                         help='Include this option to run UI in non-interactive mode')
OPTION_PARSER.add_option('-o', '--update_os', dest='update_os', action='store_true', default=False,
                         help='Update OS, highly recommended! (non-interactive mode only!)')
OPTION_PARSER.add_option('-a', '--apt_get_packages', dest='install_apt_get_packages', action='store_true',
                         default=False, help='Enable apt_get packages (' + APT_GET_PACKAGES_STR +
                                             ') install (non-interactive mode only!)')
OPTION_PARSER.add_option('-n', '--hostname', type='string', dest='change_hostname', default=None,
                         help='Enter new hostname (non-interactive mode only!)')
OPTION_PARSER.add_option('-p', '--password', type='string', dest='change_password', default=None,
                         help='Enter new password (non-interactive mode only!)')
OPTION_PARSER.add_option('-m', '--mdns', dest='install_mdns', action='store_true', default=False,
                         help='Enable mDNS server install (non-interactive mode only!)')
OPTION_PARSER.add_option('-f', '--ftp', dest='install_ftp', action='store_true', default=False,
                         help='Enable FTP server install (non-interactive mode only!)')
OPTION_PARSER.add_option('-s', '--samba', dest='install_samba', action='store_true', default=False,
                         help='Enable Samba server install (non-interactive mode only!)')
OPTION_PARSER.add_option('-v', '--vnc', dest='install_vnc', action='store_true', default=False,
                         help='Enable VNC server install (non-interactive mode only!)')

## Configuration Map ##
CONFIGURATION_MAP = OrderedDict()
# Note: Options with None value can not be enabled via command line!
CONFIGURATION_MAP['update_os'] = 'Update OS? Highly recommended!'
CONFIGURATION_MAP['install_apt_get_packages'] = 'Install apt_get packages(' + APT_GET_PACKAGES_STR + ')?'
CONFIGURATION_MAP['install_pip_packages'] = None
CONFIGURATION_MAP['change_hostname'] = 'Change hostname?'
CONFIGURATION_MAP['change_password'] = 'Change passwords?'
CONFIGURATION_MAP['install_mdns'] = 'Install mDNS server?'
CONFIGURATION_MAP['install_ftp'] = 'Install FTP server?'
CONFIGURATION_MAP['install_samba'] = 'Install Samba server?'
CONFIGURATION_MAP['install_vnc'] = 'Install VNC server?'
CONFIGURATION_MAP['update_network'] = None
CONFIGURATION_MAP['configure_uart'] = None
CONFIGURATION_MAP['configure_auto_start'] = None
CONFIGURATION_MAP['start_gate'] = None

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
## Public Functions ##
def update_os(enable_update=True):
    """ Updating OS """
    if enable_update:
        print('** Updating operating system **')
        os.system('apt-get update -y')
        os.system('apt-get dist-upgrade -y')

        try:
            import pip
        except:
            print('* Installing pip *')
            os.system('apt-get install -y python-pip')
            os.system('apt-get install -y python3-pip')

        try:
            import jinja2
        except:
            print('* Installing jinja2 *')
            os.system('apt-get install -y python-jinja2')
            os.system('apt-get install -y python3-jinja2')


def install_apt_get_packages(enable_install=True):
    """ Install apt_get packages (if needed) """
    if enable_install:
        print('** Installing apt-get packages **')
        for apt_get_package in APT_GET_PACKAGES:
            print('* Installing {} packages *'.format(apt_get_package))
            os.system('apt-get install -y ' + str(apt_get_package))


def change_password(new_password):
    """ Changing Password (if needed) """
    global password

    print('** Changing passwords **')
    users = [DEFAULT_USER, 'root']
    for user in users:
        if common.interactive:
            print("* Enter password for the user '{}' *".format(user))
        __set_password('passwd ' + user, new_password)

    password = new_password


def install_mdns(enable_install=True):
    """ Install mDNS (if needed) """
    if enable_install:
        print('** Installing mDNS server **')
        os.system('apt-get install -y avahi-daemon')
        os.system('service avahi-daemon restart')


def install_ftp(enable_install=True):
    # Installing FTP server (if needed) #
    if enable_install:
        print('** Installing FTP server **')
        os.system('apt-get install -y pure-ftpd')
        os.system('pure-pwconvert >> ' + FTP_SETTINGS_FILE)
        os.system('service pure-ftpd restart')


def install_samba(enable_install=True):
    # Configuring Samba server (if needed) #
    from jinja2 import Environment, FileSystemLoader
    jinja_environment = Environment(loader=FileSystemLoader(common.TEMPLATE_FOLDER))

    if enable_install:
        print('** Installing Samba server **')
        os.system('apt-get install -y samba')

        print('* Configuring Samba autostart *')
        samba_template = jinja_environment.get_template('smb.conf')
        samba_file_content = samba_template.render(
            hostname=common.current_hostname(DEFAULT_HOSTNAME),
            user=DEFAULT_USER,
            home_path=DEFAULT_HOME_FOLDER
        )

        samba_file = open(SAMBA_SETTINGS_FILE, 'w')
        samba_file.write(samba_file_content)
        samba_file.close()

        if common.interactive:
            print("* Enter Samba password for the user '{}' *".format(DEFAULT_USER))
        __set_password('smbpasswd -a ' + DEFAULT_USER, password)

        os.system('service smbd restart')


def install_vnc(enable_install=True):
    # Configuring VNC server (if needed) #
    from jinja2 import Environment, FileSystemLoader
    jinja_environment = Environment(loader=FileSystemLoader(common.INITD_TEMPLATE_FOLDER))

    if enable_install:
        print('** Installing VNC server **')
        os.system('apt-get install -y tightvncserver')

        print('* Configuring VNC autostart *')
        # Creating vnc daemon
        vncboot_template = jinja_environment.get_template('vncboot')
        vncboot_file_content = vncboot_template.render(
            user=DEFAULT_USER,
            vnc_settings=VNC_SETTINGS
        )

        vncboot_file = open(VNCBOOT_FILE, 'w')
        vncboot_file.write(vncboot_file_content)
        vncboot_file.close()

        # Setting permissions
        os.system('chmod 755 ' + VNCBOOT_FILE)

        # Stopping current X session
        os.system('service lightdm stop')

        # Removing X session from startup
        os.system('update-rc.d -f lightdm remove')

        # Configuring vncboot
        os.system('update-rc.d vncboot defaults')

        os.system('systemctl daemon-reload')

        if common.interactive:
            print('* Enter VNC server password (if prompted) *')
        __set_password('vncpasswd -a', password)

        print('* Configuring VNC cursor *')
        if os.path.isfile(XSTARTUP_FILE):
            overwrite = False
            with open(XSTARTUP_FILE) as xstartup_file:
                xstartup_lines = xstartup_file.readlines()

            for line_index, xstartup_line in enumerate(xstartup_lines):
                if xstartup_line.startswith('xsetroot') and VNC_CURSOR_SETTINGS not in xstartup_line:
                    overwrite = True
                    xstartup_lines[line_index] = xstartup_line.replace('\n', ' ' + VNC_CURSOR_SETTINGS + '\n')

            xstartup_file_content = ''.join(xstartup_lines)

            # Overwrite file (if needed)
            if overwrite:
                xstartup_file = open(XSTARTUP_FILE, 'w')
                xstartup_file.write(xstartup_file_content)
                xstartup_file.close()

        else:
            LOGGER.warning("Failed configuring VNC cursor. Could not find following file: '" + str(XSTARTUP_FILE) + "'!")

        # Restarting VNC
        os.system('service vncboot restart')


def update_network(network_settings):
    """ Updates network settings of the Raspberry Pi """
    if network_settings:
        print('** Updating Network Settings **')

        # Read network interface file
        if os.path.isfile(NETWORK_INTERFACES_FILE):
            # Read file lines
            with open(NETWORK_INTERFACES_FILE) as interfaces_file:
                interfaces_file_lines = interfaces_file.readlines()

            # Join file lines
            interfaces_file_content = ''.join(interfaces_file_lines)

            # Add auto eth0 (if needed)
            if 'auto eth0' not in interfaces_file_content:
                # Compose new file content
                new_interfaces_file_content = ''

                # Search for appropriate match
                for line_index, network_line in enumerate(interfaces_file_lines):
                    ip_scheme_match = re.match(
                        '^\s*iface[ ]+eth0[ ]+inet[ ]+(dhcp|static|manual)(\s*$|\s+.*?)',
                        network_line,
                        re.I
                    )

                    # Add 'auto eth0' line
                    if ip_scheme_match is not None:
                        new_interfaces_file_content += 'auto eth0\n'

                    new_interfaces_file_content += network_line

                # Overwrite network interfaces file
                if len(new_interfaces_file_content):
                    interfaces_file = open(NETWORK_INTERFACES_FILE, 'w')
                    interfaces_file.write(new_interfaces_file_content)
                    interfaces_file.close()

        # Read network dhcpcd file
        if os.path.isfile(NETWORK_SETTINGS_FILE):
            # Read file lines
            with open(NETWORK_SETTINGS_FILE) as dhcpcd_file:
                network_lines = dhcpcd_file.readlines()

            # Compose new file content
            new_dhcpcd_file_content = ''

            # Search for old dhcpcd data
            skip_lines = 0
            for line_index, network_line in enumerate(network_lines):
                ip_scheme_match = re.match('^\s*interface[ ]+eth0(\s*$|\s+.*?)', network_line, re.I)
                if ip_scheme_match is not None:

                    # Remove lines from file
                    if line_index < len(network_lines):
                        for skip_line_index in range(line_index + 1, len(network_lines)):
                            skip_line = network_lines[skip_line_index]
                            empty_line_match = re.match('^\s*$', skip_line)
                            comment_line_match = re.match('^\s*#', skip_line)
                            network_match = re.match(
                                '^\s*static[ ]+(ip_address|ip6_address|routers|domain_name_servers)=',
                                skip_line,
                                re.I
                            )

                            if empty_line_match or comment_line_match or network_match:
                                skip_lines += 1
                            else:
                                break

                elif skip_lines > 0:
                    skip_lines -= 1

                else:
                    new_dhcpcd_file_content += network_line

            # Append new data to dhcpcd file (if needed)
            if network_settings['ip_scheme'] == 'static':
                new_dhcpcd_file_content += 'interface eth0\n'
                new_dhcpcd_file_content += 'static ip_address=' + network_settings['ip_address'] + '\n'
                new_dhcpcd_file_content += '\n'

            # Overwrite dhcpcd file
            if len(new_dhcpcd_file_content):
                dhcpcd_file = open(NETWORK_SETTINGS_FILE, 'w')
                dhcpcd_file.write(new_dhcpcd_file_content)
                dhcpcd_file.close()

            # Restart network
            os.system('ip link set eth0 down')
            os.system('ip link set eth0 up')
            # os.system('service networking restart')


def configure_uart(enable_configure=True):
    """ Configuring UART on RPi3 """
    if enable_configure:
        print('** Configuring UART **')

        # Update Firmware
        __update_firmware(enable_configure)

        # Modify RPi3 config file
        if os.path.isfile(RPI3_CONFIG_FILE):
            with open(RPI3_CONFIG_FILE) as config_file:
                config_lines = config_file.readlines()

            enable_uart = False
            dtoverlay = False
            config_file_content = ''
            for line_index, config_line in enumerate(config_lines):
                append_line = True

                if 'enable_uart' in config_line:
                    append_line = False
                    if not enable_uart:
                        # Overwrite enable_uart option
                        config_file_content += 'enable_uart=1\n'
                        enable_uart = True

                dt_overlay_match = re.match(
                    '^\s*dtoverlay=(pi3-miniuart-bt-overlay|pi3-disable-bt)',
                    config_line,
                    re.I
                )

                if dt_overlay_match is not None:
                    append_line = False
                    if not dtoverlay:
                        # Overwrite dtoverlay option
                        config_file_content += 'dtoverlay=pi3-disable-bt\n'
                        dtoverlay = True

                if 'force_turbo' in config_line:
                    # Delete line
                    append_line = False

                if append_line:
                    config_file_content += config_line

            # Append needed lines if those are not found
            if not enable_uart and not dtoverlay:
                config_file_content += '# Enable UART\n'

            if not enable_uart:
                config_file_content += 'enable_uart=1\n'

            if not dtoverlay:
                config_file_content += 'dtoverlay=pi3-disable-bt\n'

            # Overwrite PRi3 config file
            if len(config_file_content):
                config_file = open(RPI3_CONFIG_FILE, 'w')
                config_file.write(config_file_content)
                config_file.close()

        # Modify RPi3 cmdline file
        if os.path.isfile(RPI3_CMDLINE_FILE):
            # Read file
            cmdline_file = open(RPI3_CMDLINE_FILE, 'r')
            cmdline_file_content = cmdline_file.read()
            cmdline_file.close()

            console_match = re.findall('\s+(console=serial[01],\d+)\s+', cmdline_file_content, re.I | re.M)
            # Disable serial console
            for console_text in console_match:
                if console_text in cmdline_file_content:
                    # Note: This will work only on latest Raspbian OS release
                    cmdline_file_content = cmdline_file_content.replace(console_text, '')

            # Overwrite PRi3 cmdline file
            cmdline_file = open(RPI3_CMDLINE_FILE, 'w')
            cmdline_file.write(cmdline_file_content)
            cmdline_file.close()

        # Stop/Disable hciuart service
        os.system('systemctl stop hciuart')
        os.system('systemctl disable hciuart')
        os.system('systemctl daemon-reload')

        # Have to reboot after configuring UART!!!
        LOGGER.warning('Please reboot Raspberry Pi in order for UART configuration to take effect!')


def configure_auto_start(enable_configure=True):
    """ Configuring auto start script """
    if enable_configure:
        print('** Configuring Automatic start **')

        file_system.copy_file(AUTO_START_TEMPLATE_FILE, AUTO_START_FILE, permissions='755')

        # Adding our script to Raspberry Pi services
        os.system('update-rc.d gate remove')
        os.system('update-rc.d gate defaults')
        os.system('systemctl daemon-reload')


def start_gate(enable_start=True):
    """ Start Gate Script """
    if enable_start:
        print('** Starting GATE **')
        # TODO: Check if instance is already running!
        if os.path.isfile(AUTO_START_FILE):
            os.system('service gate restart')

        else:
            print('Can not start GATE because it has not been configured yet!')


## Private Functions ##
def __set_password(password_command, new_password):
    """ Sets Password Command """
    if common.interactive:
        os.system(password_command)

    else:
        process = subprocess.Popen(
            password_command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        process.stdin.write(new_password + '\n')
        process.stdin.write(new_password + '\n')

        # Say no to view-only password for vncboot, otherwise should make no effect...
        process.stdin.write('n\n')

        process.stdin.flush()
        process.communicate()


def __update_firmware(enable_update=True):
    """ Updating firmware """
    if enable_update:
        print('** Updating firmware **')

        if not find_executable('rpi-update'):
            os.system('apt-get install -y rpi-update')

        os.system('rpi-update')
