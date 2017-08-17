# !/usr/bin/env python
"""
Configure Embedded Platform Script
Setup brand new embedded platform (Pi or E10) for home/industrial automation purposes
Designed to be used on a brand new system!
Use at your own risk or setup everything manually!

Project: `Bolder Automation <http://bolderautomation.net>`_
Author: `Kirill V. Belyayev <http://kbelyayev.com>`_
"""

### INCLUDES ###
import sys
import os
import shutil
import zipfile
import subprocess
import logging

from distutils.spawn import find_executable


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def upgrade_py_knife():
    """ Attempting to upgrade/install py_knife package """
    __install_pip()

    try:
        import py_knife

    except:
        print('** Installing py_knife **')
        os.system('pip install py_knife')

    else:
        print('** Upgrading py_knife **')
        os.system('pip install --upgrade py_knife')


def configure_system(configuration_options):
    """ Configure Embedded System script """
    from py_knife import platforms

    import common

    if platforms.PLATFORM in platforms.EMBEDDED_PLATFORMS:
        if platforms.PLATFORM == platforms.RASPBERRY_PI:
            print('*** Configuring Raspberry Pi ***')
            import configure_pi as configure_module

        else:
            print('*** Configuring Synapse E10 ***')
            import configure_e10 as configure_module

        if 'interactive' in configuration_options:
            common.interactive = configuration_options['interactive']

        if hasattr(configure_module, 'CONFIGURATION_MAP'):
            configuration_map = getattr(configure_module, 'CONFIGURATION_MAP')

            for configuration_step, configure_step_message in configuration_map.items():
                if configuration_step in configuration_options.keys():
                    if hasattr(configure_module, configuration_step):
                        proceed_w_step = __proceed_w_step(
                            configure_step_message,
                            configuration_options[configuration_step]
                        )

                        if bool(proceed_w_step):
                            configuration_function = getattr(configure_module, configuration_step)
                            configuration_function(proceed_w_step)

                    else:
                        LOGGER.warning("Function '" + str(configuration_step) + "' does not exist!")

                elif configure_step_message is not None:
                    LOGGER.warning("Configuration options are missing following key'" + str(configuration_step) + "'!")

        else:
            LOGGER.error("Configuration Module '" + str(configure_module.__name__) + "' is missing configuration map!")


def clean_system(remove_database=True, remove_logs=True, overwrite_scripts=False):
    """ Cleans system files (gate files on the system) """
    from py_knife import file_system

    from gate.common import CWD, GATE_FOLDER, DOCS_FOLDER, LOGS_FOLDER, UPLOADS_FOLDER
    from gate.common import DATABASE_FOLDER, SYSTEM_FOLDER, HEADERS_FOLDER
    from common import copy_files_w_permissions

    if remove_database:
        ## Removing obsolete database data ##
        # Note: Might not work properly on running system
        print('*** Removing obsolete database ***')
        file_system.remove_dir(DATABASE_FOLDER)

    if remove_logs:
        ## Removing obsolete log data ##
        # Note: Might not work properly on running system
        print('*** Removing obsolete logs ***')
        file_system.remove_dir(LOGS_FOLDER)

    print('*** Creating folders for user data ***')
    file_system.make_dir(GATE_FOLDER)
    file_system.make_dir(LOGS_FOLDER)
    file_system.make_dir(UPLOADS_FOLDER)
    file_system.make_dir(DATABASE_FOLDER)
    file_system.make_dir(SYSTEM_FOLDER)
    file_system.make_dir(HEADERS_FOLDER)

    if overwrite_scripts:
        print('*** Overwriting GATE scripts ***')
        gate_script_files = [('run_gate.py', '755'), ('reset_gate.py', '755'), ('ip_addr_utility.py', '755')]
        copy_files_w_permissions(gate_script_files, '', CWD)

        # Copying documentation and system data
        file_system.copy_dir('docs', DOCS_FOLDER)
        file_system.copy_dir('system', SYSTEM_FOLDER)
        file_system.copy_dir('headers', HEADERS_FOLDER)


## Private Functions ##
def __install_pip():
    """ Attempting to install pip """
    try:
        import pip

    except:
        if find_executable('apt-get'):
            print('** Installing pip **')
            os.system('apt-get install -y python-pip')
            os.system('apt-get install -y python3-pip')

        else:
            if os.name == 'posix':
                # Assuming the worst, we are running on E10!
                file_system_root = os.path.abspath(os.sep)
                python_version = 'python' + str(sys.version_info[0]) + '.' + str(sys.version_info[1])
                patch_path = os.path.join(file_system_root, 'usr', 'include', python_version)
                patch_file_path = os.path.join(patch_path, 'pyconfig.h')
                if not os.path.isfile(patch_file_path):
                    print('** Patching python **')
                    if not os.path.isdir(patch_path):
                        os.makedirs(patch_path)

                    if not os.path.isfile(patch_file_path):
                        new_file = open(patch_file_path, 'a')
                        new_file.close()

            print('** Installing setuptools **')
            cwd = sys.path[0]
            package_name = 'setuptools-0.6c11'
            zip_path = os.path.join(os.path.dirname(__file__), 'linux', package_name + '.zip')

            try:
                zip_archive = zipfile.ZipFile(zip_path, 'r')
                zip_archive.extractall(cwd)
                zip_archive.close()

                package_path = os.path.join(cwd, package_name)
                os.chdir(package_path)

                print('Installing {} ...'.format(package_name))
                if os.name == 'nt':
                    # This failed on E10 as part of web interface install
                    install_process = subprocess.Popen(['python', 'setup.py', 'install'], shell=True)
                else:
                    # Proven to work robust on E10 (but fails on Windows)
                    install_process = subprocess.Popen(['python setup.py install'], shell=True)

                install_process.wait()
                os.chdir(cwd)

                print('Cleaning {} up ...'.format(package_name))
                if os.path.isdir(package_path):
                    shutil.rmtree(package_path)

                print('** Installing pip **')
                os.system('easy_install pip==1.4.1')

            except:
                LOGGER.warning('Unable to install/upgrade py_knife! Pip is not installed!')


def __proceed_w_step(user_question, default):
    """ Asks user if they want to proceed """
    from common import interactive

    output = default

    if interactive and user_question is not None:
        # Fix Python 2.x.
        try:
            input = raw_input
        except NameError:
            pass

        response = input(user_question + ' (y/n): ')
        output = bool('y' in response.lower())

    return output


### MAIN ###
if __name__ == '__main__':
    # Setup Logger
    logging.basicConfig(level=logging.ERROR)

    # Adding py_knife (if needed)
    upgrade_py_knife()

    from py_knife import platforms

    if platforms.PLATFORM in platforms.EMBEDDED_PLATFORMS:
        if platforms.PLATFORM == platforms.RASPBERRY_PI:
            import configure_pi as configure_module
        else:
            import configure_e10 as configure_module

        if hasattr(configure_module, 'OPTION_PARSER'):
            option_parser = getattr(configure_module, 'OPTION_PARSER')

            if os.geteuid() == 0 or 'SUDO_UID' in os.environ.keys():
                # Get system options from options parser
                configure_options, args = option_parser.parse_args()

                # Run Configure Raspberry Pi script
                configure_system(vars(configure_options))

                print('Please restart your machine!')

            else:
                LOGGER.error('Could not configure OS: Please run script as root!')

        else:
            LOGGER.error("Configuration Module '" + str(configure_module.__name__) + "' is missing option parser!")
    else:
        LOGGER.error('Could not configure OS: Only Raspberry Pi/Synapse E10 is supported at the moment!')
