"""
Some common configure constants, functions, etc
"""

### INCLUDES ###
import os
# import sys
import re
import logging


### CONSTANTS ###
## OS Files/Folders ##
FILE_SYSTEM_ROOT = os.path.abspath(os.sep)
ETC_FOLDER = os.path.join(FILE_SYSTEM_ROOT, 'etc')
INITD_FOLDER = os.path.join(ETC_FOLDER, 'init.d')
HOSTS_FILE = os.path.join(ETC_FOLDER, 'hosts')
HOSTNAME_FILE = os.path.join(ETC_FOLDER, 'hostname')

## Template Folders ##
TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), 'linux')
ETC_TEMPLATE_FOLDER = os.path.join(TEMPLATE_FOLDER, 'etc')
INITD_TEMPLATE_FOLDER = os.path.join(TEMPLATE_FOLDER, 'init.d')

## Globals ##
interactive = False

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
## File System Functions ##
def install_pip_packages(enable_install=True):
    """ Install pip packages (if needed) """
    # from py_knife import platforms, file_system
    # from py_knife.zip import extract_zip
    # from py_knife.py_install import install_package
    #
    # from gate.common import CWD

    if enable_install:
        print "** Installing pip packages **"

        try:
            import bottle
        except:
            print "* Installing bottle *"
            os.system('pip install bottle==0.11.6')

        try:
            import pymodbus
        except:
            print "* Installing pymodbus *"
            os.system('pip install --no-deps pymodbus==1.2.0')

        try:
            import serial
        except:
            print "* Installing pyserial *"
            os.system('pip install pyserial==2.7')

        try:
            import tornado
        except:
            print "* Installing tornado *"
            # # Old Tornado install (Made for Synapse E10)
            # if platforms.PLATFORM == platforms.SYNAPSE_E10:
            #     os.system('pip install tornado==2.4.1')
            #     # Patching netutil files
            #     import tornado
            #     tornado_path = os.path.dirname(tornado.__file__)
            #
            #     # Remove old netutil files
            #     netutil_files_path = os.path.join(tornado_path, 'netutil.*')
            #     file_system.remove_files(netutil_files_path)
            #
            #     # Replace netutil file
            #     source_netutil = os.path.join(TEMPLATE_FOLDER, 'netutil.py')
            #     destination_netutil = os.path.join(tornado_path, 'netutil.py')
            #     file_system.copy_file(source_netutil, destination_netutil)

            # New Tornado install
            # FIXME: Gate Upload still crashes sometimes (need more investigation)
            os.system('pip install tornado==4.4.1')

        try:
            import pyasn1
        except:
            print "* Installing pyasn1 *"
            os.system('pip install pyasn1==0.1.7')

        try:
            import pysnmp
        except:
            print "* Installing pysnmp *"
            os.system('pip install --no-deps pysnmp==4.2.5')

        try:
            import Crypto
        except:
            print "* Installing pycrypto *"
            os.system('pip install pycrypto')

        try:
            import snapconnect
        except:
            print "* Installing Snap Connect *"
            # Old Snap Connect install
            # package_name = 'snapconnect-3.1.0'
            # # FIXME: Gate does not work with snapconnect-3.2.0 as of now
            # # package_name = 'snapconnect-3.2.0'
            # zip_path = os.path.join(TEMPLATE_FOLDER, package_name + '.zip')
            # if os.path.isfile(zip_path):
            #     cwd = sys.path[0]
            #     success = extract_zip(zip_path, cwd)
            #
            #     if success:
            #         if platforms.PLATFORM != platforms.SYNAPSE_E10:
            #             print "* Copying Demo License *"
            #             _license_path = os.path.join(package_name, 'license.dat')
            #             license_path = os.path.join(package_name, 'License.dat')
            #             # Rename if needed (thanks Synapse for all the inconsistencies! Love you guys!)
            #             if os.path.isfile(_license_path):
            #                 os.rename(_license_path, license_path)
            #             file_system.copy_file(license_path, CWD)
            #
            #         install_package(package_name)

            # New Snap Connect install
            os.system('pip install --extra-index-url https://update.synapse-wireless.com/pypi snapconnect==3.6.1')


## Hostname Functions ##
def valid_hostname(input_hostname):
    output = False
    if len(input_hostname) <= 255:
        # strip exactly one dot from the right, if present
        if input_hostname[-1] == '.':
            input_hostname = input_hostname[:-1]

        allowed = re.compile('(?!-)[A-Z\d-]{1,63}(?<!-)$', re.I)
        output = all(allowed.match(x) for x in input_hostname.split('.'))

    return output


def current_hostname(default_hostname=None):
    """ Change hostname (if needed) """
    # Read hostname file
    if os.path.isfile(HOSTNAME_FILE):
        hosts_file = open(HOSTNAME_FILE, 'r')
        output = hosts_file.read()
        hosts_file.close()

    else:
        output = default_hostname

    return output


def change_hostname(new_hostname):
    """ Change hostname (if needed) """
    _current_hostname = current_hostname()

    print '** Changing hostname **'
    # Read file
    hosts_file = open(HOSTS_FILE, 'r')
    hosts_file_content = hosts_file.read()
    hosts_file.close()

    if _current_hostname in hosts_file_content:
        if interactive:
            new_hostname = raw_input('Enter new hostname: ')

        if valid_hostname(new_hostname):
            os.system('hostname ' + new_hostname)

            # Overwrite files
            hosts_file_content = hosts_file_content.replace(_current_hostname, new_hostname)

            hosts_file = open(HOSTS_FILE, 'w')
            hosts_file.write(hosts_file_content)
            hosts_file.close()

            hostname_file = open(HOSTNAME_FILE, 'w')
            hostname_file.write(new_hostname)
            hostname_file.close()

            print "Hostname changed to '" + str(new_hostname) + "'!"

        else:
            LOGGER.error("Provided hostname '" + str(new_hostname) + "' is invalid!")

    else:
        LOGGER.error("Could not change hostname! Script was not able to find current hostname!")


## File System Functions ##
def copy_files_w_permissions(files_w_permissions, source_folder, destination_folder):
    """ Copies files with provided permissions """
    from py_knife import file_system

    file_system.make_dir(destination_folder)

    for ip_utility_file, permissions in files_w_permissions:
        _source_folder = os.path.join(source_folder, ip_utility_file)
        _destination_folder = os.path.join(destination_folder, ip_utility_file)
        file_system.copy_file(_source_folder, _destination_folder, permissions)
