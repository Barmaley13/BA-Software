# !/usr/bin/env python
"""
Gate Setup Scripts
"""

### INCLUDES ###
import os
import sys
import imp
import glob
import copy
import shutil
import pkgutil

from distutils.core import setup
from distutils.command.install_data import install_data
from distutils.command.install import install


### CONSTANTS ###
## INSTALLATION/DISTRIBUTION OPTIONS ##
# Generic Options #
REMOVE_DATABASE = True
REMOVE_LOGS = False

## Default Configure Options ##
DEFAULT_CONFIGURE_OPTIONS = {
    'interactive': False,
    'update_os': True,
    'install_pip_packages': True,
    'change_hostname': 'gate',
    'change_password': None,
    'configure_ip_utility': True,       # Works only on E10 #
    'update_network': False,
    'install_mdns': True,               # Works only on RPi3 #
    'install_ftp': True,
    'install_samba': False,             # Works only on RPi3 #
    'install_vnc': False,               # Works only on RPi3 #
    'configure_auto_start': True,
    # Keep this off! (Gate instance is already running most likely!)
    'start_gate': False,
}

# Base and Node Distributions #
# Note: Base and Node software updates only work using Web Interface
INCLUDE_BASE = True
BASE_PATHS = [os.path.join('..', 'Distributions', 'Base', 'BASE_2.06.spy')]
INCLUDE_NODE = True
NODE_PATHS = [
    os.path.join('..', 'Distributions', 'Node', 'default', 'NODE_2.06.spy'),
    os.path.join('..', 'Distributions', 'Node', 'jowa-102', 'NODE_2.06.spy'),
    os.path.join('..', 'Distributions', 'Node', 'swe-101', 'NODE_2.06.spy')
]

# Distribution Path #
DIST_PATH = os.path.join('..', 'Distributions', 'Gate')

# System Data #
SYSTEM_NAME = 'swe'

## Internal Constants ##
CWD = sys.path[0]
# print('CWD: {}'.format(CWD))
# Set current working directory #
os.chdir(CWD)


### FUNCTIONS ###
def copy_dir(source_path, destination_path):
    # LOGGER.debug('source: ' + str(source_path))
    # LOGGER.debug('destination: ' + str(destination_path))
    if os.path.isdir(source_path):
        os.makedirs(destination_path)
        sub_items = glob.glob(os.path.join(source_path, '*'))
        for sub_item_path in sub_items:
            sub_item_name = os.path.basename(sub_item_path)
            copy_dir(sub_item_path, os.path.join(destination_path, sub_item_name))

    elif os.path.isfile(source_path):
        shutil.copy(source_path, destination_path)


if len(sys.argv):
    if 'install' in sys.argv:
        # That way we are using functions from new distribution and not old one!
        if not os.path.isfile('version.py'):
            shutil.copy(os.path.join('gate', '__init__.py'), 'version.py')

        if not os.path.isdir('configure'):
            copy_dir(os.path.join('gate', 'configure'), 'configure')

        from version import __version__
        import configure

    else:
        from gate import __version__, configure

else:
    from gate import __version__, configure


## Install/Upgrade py_knife ##
configure.upgrade_py_knife()


### INCLUDES (cont) ###
from py_knife import platforms, py_setup, file_system


### FUNCTIONS (cont) ###
## Dist Functions ##
def _create_dist_options():
    """ Creates distribution options """
    print('Remove Database: {}'.format(REMOVE_DATABASE))
    if REMOVE_DATABASE:
        file_system.make_dir('database')
        file_system.make_file(os.path.join('database', 'dummy.txt'))

    print('Remove Logs: {}'.format(REMOVE_LOGS))
    if REMOVE_LOGS:
        file_system.make_dir('logs')
        file_system.make_file(os.path.join('logs', 'dummy.txt'))

    print('Include Base Software: {}'.format(INCLUDE_BASE))
    if INCLUDE_BASE:
        file_system.make_dir('base')
        for base_source in BASE_PATHS:
            base_destination = os.path.join('base', os.path.basename(base_source))
            file_system.copy_file(base_source, base_destination)

    print('Include Node Software: {}'.format(INCLUDE_NODE))
    if INCLUDE_NODE:
        file_system.make_dir('node')
        for node_source in NODE_PATHS:
            node_destination = os.path.join('node', os.path.basename(os.path.dirname(node_source)))
            file_system.make_dir(node_destination)
            node_destination = os.path.join(node_destination, os.path.basename(node_source))
            file_system.copy_file(node_source, node_destination)


## Install Functions ##
def _pre_install():
    """ Pre install procedures """
    print('*** Installing missing python packages ***')

    configure_options = copy.deepcopy(DEFAULT_CONFIGURE_OPTIONS)
    configure.configure_system(configure_options)

    print('*** Removing obsolete gate packages ***')
    _uninstall_obsolete_gate()


def _uninstall_obsolete_gate():
    """ Uninstalls obsolete gate package (if needed) """
    clean_install = True

    try:
        while True:
            f, gate_path, desc = imp.find_module('gate', sys.path[1:])
            print("Removing obsolete gate package located at '{}'".format(gate_path))
            clean_install = file_system.remove_dir(gate_path)
            f.close()

    except:
        if clean_install:
            print('Nothing to remove - clean install!')


def _post_install():
    """ Post install procedures """
    configure.clean_system(REMOVE_DATABASE, REMOVE_LOGS, overwrite_scripts=True)


### CLASSES ###
class MyInstallData(install_data):
    def run(self):
        # need to change self.install_dir to the library dir
        install_cmd = self.get_finalized_command('install')
        self.install_dir = getattr(install_cmd, 'install_lib')
        return install_data.run(self)


class MyInstall(install):
    def run(self):
        """ Modified install procedure """
        _pre_install()
        print('*** Installing gate package ***')
        install.run(self)
        _post_install()


### SETUP PROCEDURES ###
packages = py_setup.find_packages(".", "")
# print('packages: {}\n'.format(packages))

if len(sys.argv):
    if 'sdist' in sys.argv:
        print('*** Generating Documentation ***')
        py_setup.generate_docs(packages)

        print('*** Creating distribution options ***')
        _create_dist_options()

        # Change default distribution folder
        sys.argv.append('--dist-dir=' + str(DIST_PATH))

        print('*** Generation Distribution ***')

    elif 'install' in sys.argv:
        # Enable force to overwrite existing files and create folders
        sys.argv.append('--force')

data_files = (py_setup.non_python_files('gate', ignore_dirs=['obsolete', 'source']))
# print('data_files: {}\n'.format(data_files))

package_data_content = py_setup.package_data_files('docs')
if REMOVE_DATABASE:
    package_data_content += py_setup.package_data_files('database')
if REMOVE_LOGS:
    package_data_content += py_setup.package_data_files('logs')

package_data = {'': package_data_content}
# print('package_data: {}\n'.format(package_data))

setup(
    name='gate',
    version=__version__,
    description='Sleepy Mesh, Gate Portion',
    long_description='Highly flexible & customizable low power Wireless Mesh Network System',
    author='Kirill V. Belyayev',
    author_email='kirill@bolder-automation.io',
    url='http://bolder-automation.io',
    packages=packages.keys(),
    package_dir=packages,
    package_data=package_data,
    data_files=data_files,
    cmdclass={'install_data': MyInstallData, 'install': MyInstall},
    requires=[
        'pip (>=1.4.1)',
        'bottle (==0.11.6)',
        'pymodbus (==1.2.0)',
        'pyserial (==2.7)',
        'tornado (==4.4.1)',
        'pyasn1 (==0.1.7)',
        'pysnmp (==4.2.5)',
        'pycrypto (>=2.1.0)',
        'py_knife (>=0.01.23)',
        'snapconnect (==3.6.1)'
    ]
)

if len(sys.argv):
    if 'sdist' in sys.argv:
        from py_knife import aes, file_system

        ## Extracting disto_password ##
        DEFAULT_SYSTEM_DATA = dict()
        for importer, module_name, is_package in pkgutil.iter_modules(['system']):
            if not is_package:
                system_name = module_name.split('.')[-1]
                if not system_name.startswith('_'):
                    handler_module = importer.find_module(module_name).load_module(module_name)
                    DEFAULT_SYSTEM_DATA[system_name] = handler_module.SYSTEM_DATA

        if SYSTEM_NAME in DEFAULT_SYSTEM_DATA:
            system_data = DEFAULT_SYSTEM_DATA[SYSTEM_NAME]
        else:
            system_data = DEFAULT_SYSTEM_DATA['default']

        distro_password = system_data['distro_password']

        print('*** Encrypting Distribution ***')
        if 'DIST_PATH' not in globals().keys():
            dist_path = 'dist'

        else:
            dist_path = DIST_PATH

        py_dist = os.path.join(CWD, dist_path, 'gate-' + __version__)

        print('py_dist: {}'.format(py_dist))

        aes.encrypt(py_dist + '.zip', py_dist + '.pea', distro_password)

        print('*** Cleaning Up ***')
        for package_path in packages.values():
            pyc_files = glob.glob(os.path.join(package_path, '*.pyc'))
            for pyc_file in pyc_files:
                file_system.remove_file(pyc_file)

        file_system.remove_file('MANIFEST')

        if REMOVE_DATABASE:
            file_system.remove_dir('database')

        if REMOVE_LOGS:
            file_system.remove_dir('logs')

        if INCLUDE_BASE:
            file_system.remove_dir('base')

        if INCLUDE_NODE:
            file_system.remove_dir('node')

    elif 'install' in sys.argv:
        print('*** Cleaning Up ***')
        for clean_up_dir in ('build', 'configure'):
            file_system.remove_dir(clean_up_dir)

        for clean_up_file_name in ('version', ):
            for clean_up_file_extension in ('.py', '.pyc'):
                clean_up_file_path = clean_up_file_name + clean_up_file_extension
                file_system.remove_file(clean_up_file_path)
