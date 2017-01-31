"""
Configure Synapse E10 Script
Project: `Bolder Automation <http://bolder-automation.io>`_
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""


### INCLUDES ###
import os
import sys
import logging

from optparse import OptionParser

import bottle

from py_knife import file_system
from py_knife.ordered_dict import OrderedDict

from gate.common import FILE_SYSTEM_ROOT, TPL_FOLDER

import common
from common import install_pip_packages, change_hostname


### CONSTANTS ###
## OS Files/Folders ##
IP_ADDR_FOLDER = os.path.join(FILE_SYSTEM_ROOT, 'home', 'ip_addr')
NETWORK_SETTINGS_FILE = os.path.join(common.INITD_FOLDER, 'S40network')
FTP_FILE = os.path.join(common.INITD_FOLDER, 'ftp')
AUTO_START_FILE = os.path.join(common.INITD_FOLDER, 'S999snap')

## Template Folders ##
IP_ADDR_TEMPLATE_FOLDER = os.path.join(common.TEMPLATE_FOLDER, 'ip_addr')
FTP_TEMPLATE_FILE = os.path.join(common.INITD_TEMPLATE_FOLDER, 'ftp')
AUTO_START_TEMPLATE_FILE = os.path.join(common.INITD_TEMPLATE_FOLDER, 'S999snap')

## Option Parser ##
OPTION_PARSER = OptionParser()
OPTION_PARSER.add_option('-d', '--disable_interactive', dest='interactive', action='store_false', default=True,
                         help='Include this option to run UI in non-interactive mode')
OPTION_PARSER.add_option('-o', '--update_os', dest='update_os', action='store_true', default=False,
                         help='Update OS, highly recommended! (non-interactive mode only!)')
OPTION_PARSER.add_option('-n', '--hostname', type='string', dest='change_hostname', default=None,
                         help='Enter new hostname (non-interactive mode only!)')
OPTION_PARSER.add_option('-f', '--ftp', dest='install_ftp', action='store_true', default=False,
                         help='Enable FTP server install (non-interactive mode only!)')

## Configuration Map ##
CONFIGURATION_MAP = OrderedDict()
# Note: Options with None value can not be enabled via command line!
CONFIGURATION_MAP['update_os'] = 'Update OS? Highly recommended!'
CONFIGURATION_MAP['install_pip_packages'] = None
CONFIGURATION_MAP['change_hostname'] = 'Change hostname?'
CONFIGURATION_MAP['configure_ip_utility'] = None
CONFIGURATION_MAP['install_ftp'] = 'Install FTP server?'
CONFIGURATION_MAP['update_network'] = None
CONFIGURATION_MAP['configure_auto_start'] = None
CONFIGURATION_MAP['start_gate'] = None

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
## Public Functions ##
def update_os(enable_update=True):
    """ Updating OS """
    from py_knife.zip import extract_zip
    from py_knife.py_install import install_package

    if enable_update:
        print '** Updating operating system **'
        __patch_python()

        try:
            import pip
        except:
            print "* Installing setuptools *"
            package_name = 'setuptools-0.6c11'
            zip_path = os.path.join(common.TEMPLATE_FOLDER, package_name + '.zip')

            cwd = sys.path[0]
            success = extract_zip(zip_path, cwd)
            if success:
                install_package(package_name)

                print "* Installing pip *"
                os.system('easy_install pip==1.4.1')


def configure_ip_utility(enable_configure=True):
    """ Configuring IP utility """
    if enable_configure:
        print "** Configuring IP Addressing Utility **"
        ip_addr_files = [('issue', '664'), ('passwd', '644')]    # ('group', '664')
        common.copy_files_w_permissions(ip_addr_files, common.ETC_TEMPLATE_FOLDER, common.ETC_FOLDER)

        ip_addr_user_files = [('.ash_history', '664'), ('.profile', '664')]
        common.copy_files_w_permissions(ip_addr_user_files, IP_ADDR_TEMPLATE_FOLDER, IP_ADDR_FOLDER)


def install_ftp(enable_install=True):
    # Installing FTP server (if needed) #
    if enable_install:
        print '** Installing FTP server **'
        try:
            import pyftpdlib

        except:
            print "** Installing pyftpdlib **"
            os.system('pip install pyftpdlib==0.7')

        file_system.copy_file(FTP_TEMPLATE_FILE, FTP_FILE, '755')

        print "** Restarting FTP server **"
        if os.path.isfile(FTP_FILE):
            os.system(FTP_FILE + ' restart')


def update_network(network_settings, template_path=None):
    """ Updates network settings of the Synapse E10 """
    print "** Updating Network Settings **"
    if template_path is None:
        template_path = os.path.join('gate', 'tpl', 'network_daemon')
        if not os.path.isfile(template_path):
            bottle.TEMPLATE_PATH.append(TPL_FOLDER)
            template_path = 'network_daemon'

    ip_content = bottle.template(template_path, settings=network_settings)
    file_system.save_file(NETWORK_SETTINGS_FILE, ip_content, '755')

    # print "** Restarting network **"
    if os.path.isfile(NETWORK_SETTINGS_FILE):
        os.system(NETWORK_SETTINGS_FILE + ' restart')


def configure_auto_start(enable_configure=True):
    """ Configuring auto start script """
    if enable_configure:
        print "** Configuring Automatic start **"
        file_system.copy_file(AUTO_START_TEMPLATE_FILE, AUTO_START_FILE, permissions='755')


def start_gate(enable_start):
    """ Start Gate Script """
    if enable_start:
        print "** Starting GATE **"
        # TODO: Check if instance is already running!
        if os.path.isfile(AUTO_START_FILE):
            os.system(AUTO_START_FILE + ' restart')

        else:
            print "Can not start GATE because it has not been configured yet!"


## Private Functions ##
def __patch_python():
    """ E10 Python Patch """
    python_version = 'python' + str(sys.version_info[0]) + '.' + str(sys.version_info[1])
    patch_path = os.path.join(FILE_SYSTEM_ROOT, 'usr', 'include', python_version)
    patch_file_path = os.path.join(patch_path, 'pyconfig.h')
    if not os.path.isfile(patch_file_path):
        print "* Patching python *"
        file_system.make_dir(patch_path)
        file_system.make_file(patch_file_path)
