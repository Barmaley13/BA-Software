"""
Complex Uploader Class, handles gate upload
"""

### INCLUDES ###
import os
import glob
import logging

from py_knife import platforms, aes, file_system, py_install, zip
from py_knife.decorators import simple_decorator

from gate import common, strings

from .snap_uploader import UPLOAD_CANCELLED, UPLOAD_SUCCESS
from .snap_uploader import CALLBACK_MESSAGES, SUCCESS, UPLOAD_UNKNOWN
from .simple_uploader import SimpleUploader


### CONSTANTS ###
## Strings ##
# Errors #
ZIP_ERROR = "Could not unpack software properly!"
NODE_ERROR = "Node software is not found! Update package is corrupt!"
FILE_ERROR = "Filesystem error!"

# Status Messages #
INSTALLING_GATE1 = "Installing "
INSTALLING_GATE2 = " software." + strings.SOME_TIME
RESETTING_BRIDGE = 'Resetting bridge to network defaults...'
RESETTING_NODE = 'Resetting field unit!'

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
# Complex Upload Decorator #
@simple_decorator
def parse_upload_folders(func):
    """ Decorator to parse uploads folders """
    def _parse_upload_folders(*args, **kwargs):

        kwargs['continue_complex_upload'] = True
        kwargs['break'] = False

        zip_dirs = glob.glob(os.path.join(common.UPLOADS_FOLDER, args[0].zip_name, '*'))
        for zip_dir in zip_dirs:
            kwargs['zip_dir'] = zip_dir
            kwargs['dir_name'] = os.path.basename(zip_dir).lower()
            LOGGER.debug('dir_name: ' + kwargs['dir_name'])

            kwargs = func(*args, **kwargs)

            if kwargs['break']:
                break

        return kwargs['continue_complex_upload']

    return _parse_upload_folders


### CLASSES ###
# TODO: Make and run uploader as a thread. So web interface stays responsive during the update process
class ComplexUploader(SimpleUploader):
    def __init__(self, manager):
        super(ComplexUploader, self).__init__(manager)

        # Cancel Update #
        self.cancel_complex_upload = False

        # Path to zip archive
        self._zip_path = ''
        # Name of the zip file (without extension)
        self.zip_name = ''              # used by parse_upload_folders decorator

        self._steps_queue = list()

        # Progress related members
        self._current_step = 0.0
        self._total_steps = 0.0

        # Reboot Related
        self._reboot_ack = False

    ## Complex Upload Methods ##
    def complex_upload(self, file_path=None):
        """
        Complex Upload. Called multiple times.
        Clean up routines delete folders from unpacked software update archive.
        And indicates what part of the update process have been executed already
        """
        LOGGER.debug('Complex Upload')

        # Init complex upload
        if file_path is not None:
            self._zip_path = file_path
            file_name = os.path.basename(file_path)
            self.zip_name = os.path.splitext(file_name)[0]
            self._steps_queue = [
                self._unpack_archive,
                self._set_progress,
                self._update_nodes,
                self._update_base,
                self._update_gate,
                self._reset_bridge,
                self._request_reboot_ack,
                self._wait_for_reboot_ack,
                self._delete_logs,
                self._update_gate_time,
                self._delete_database
            ]

            LOGGER.debug("self.zip_name = " + self.zip_name)

            self._total_nodes = len(self._targets)
            self._current_step = 0.0
            self._total_steps = 0.0

            self.cancel_complex_upload = False
            self._reboot_ack = False

        else:
            self._current_step += 1.0

        # Check if user is cancelling procedure
        if self.cancel_complex_upload:
            self.finish_upload(UPLOAD_CANCELLED, False)

        else:
            # Perform complex upload steps
            while len(self._steps_queue):
                if not self._steps_queue[0]():
                    break

                # Move to the next one
                del self._steps_queue[0]

            else:
                # Global Clean Up #
                if not file_system.empty_dir(common.UPLOADS_FOLDER):
                    return False

                # Reboot #
                self._manager.reboot()

        return False

    def reboot_ack(self):
        """ Sets reboot flag in order to trigger reboot """
        if self._manager.reboot_flag:
            self._reboot_ack = True
            self.complex_upload()

    # Complex Upload Steps #
    def _unpack_archive(self):
        """ Unpack the archive """
        continue_complex_upload = True
        LOGGER.debug('_unpack_archive')

        if os.path.isfile(self._zip_path):
            distribution_path, distribution_ext = os.path.splitext(self._zip_path.lower())
            LOGGER.debug("distribution_ext = " + distribution_ext)

            # Check Extension
            clean_up = False
            if distribution_ext in ('.zip', '.vol', '.pea'):
                first_path = second_path = distribution_path + distribution_ext
                if distribution_ext == '.vol':
                    distro_password = self._manager.system_settings.distro_password
                    clean_up = zip.extract_zip(first_path, password=distro_password)
                    second_path = distribution_path + '.pkg'
                elif distribution_ext == '.pea':
                    distro_password = self._manager.system_settings.distro_password
                    second_path = distribution_path + '.zip'
                    clean_up = aes.decrypt(first_path, second_path, distro_password)
                elif distribution_ext == '.zip':
                    clean_up = True
                    # second_path = first_path

                if clean_up:
                    clean_up = zip.extract_zip(second_path)

            if clean_up:
                # Clean Up #
                file_system.remove_file(self._zip_path)

            else:
                self.finish_upload(FILE_ERROR, False)
                continue_complex_upload = False

        return continue_complex_upload

    def _set_progress(self):
        """ Set some progress members (if needed) """
        continue_complex_upload = True
        LOGGER.debug('_set_progress')

        if self._current_step == 0.0 and self._total_steps == 0.0:
            self._current_step += 1.0
            self._total_steps += 1.0

            self.__set_progress()

        LOGGER.debug("self._current_step = " + str(self._current_step))
        LOGGER.debug("self._total_steps = " + str(self._total_steps))

        return continue_complex_upload

    @parse_upload_folders
    def __set_progress(self, **kwargs):
        """ Set progress members, inner method """
        if kwargs['dir_name'] in ('node', 'base', 'gate'):
            total_step_increment = 1.0
            if kwargs['dir_name'] == 'node' and not len(self._targets):
                total_step_increment = 0.0
            self._total_steps += total_step_increment

        return kwargs

    @parse_upload_folders
    def _update_nodes(self, **kwargs):
        """ Update Nodes (if needed) """
        LOGGER.debug('_update_nodes')

        if kwargs['dir_name'] == 'node':
            if len(self._targets):
                for target_index, target in enumerate(self._targets):
                    file_path = ""

                    node_platform = target['raw_platform'].split('-')
                    if len(node_platform) > 1:
                        node_platform = node_platform[0] + '-' + node_platform[1]
                    else:
                        node_platform = node_platform[0]

                    # Determine what file to use
                    node_paths = glob.glob(os.path.join(kwargs['zip_dir'], '*'))

                    # Try to match folder names to the platform of the node
                    for node_path in node_paths:
                        dir_name = os.path.basename(node_path).lower()
                        if dir_name == node_platform:
                            file_path = glob.glob(os.path.join(node_path, '*.spy'))[0]
                            break

                    # Using default
                    else:
                        default_path = os.path.join(kwargs['zip_dir'], 'default')
                        if os.path.isdir(default_path):
                            default_path = glob.glob(os.path.join(default_path, '*.spy'))[0]
                            if os.path.isfile(default_path):
                                file_path = default_path

                    LOGGER.debug('target = ' + str(target))
                    LOGGER.debug('file_path = ' + file_path)

                    # If file_path is unknown here, prompt an error
                    if file_path == "":
                        self.finish_upload(NODE_ERROR, False)
                        kwargs['continue_complex_upload'] = False
                        break

                    else:
                        target['_index'] = target_index
                        target['_path'] = file_path

                else:
                    self.simple_upload()
                    kwargs['continue_complex_upload'] = False

            # Clean up
            elif not self._clean_up('node'):
                kwargs['continue_complex_upload'] = False

            kwargs['break'] = True

        return kwargs

    @parse_upload_folders
    def _update_base(self, **kwargs):
        """ Update Base Node (if needed) """
        LOGGER.debug('_update_base')

        if kwargs['dir_name'] == 'base':
            base_path = glob.glob(os.path.join(kwargs['zip_dir'], '*.spy'))[0]
            self._manager.bridge.base['_index'] = 0
            self._manager.bridge.base['_path'] = base_path
            # Just in case
            del self._targets[:]
            self._targets.append(self._manager.bridge.base)
            self.simple_upload()

            kwargs['continue_complex_upload'] = False
            kwargs['break'] = True

        return kwargs

    @parse_upload_folders
    def _update_gate(self, **kwargs):
        """ Update Gate (if needed) """
        LOGGER.debug('_update_gate')

        if kwargs['dir_name'] == 'gate':
            package_name = self.zip_name
            package_path = os.path.join(common.UPLOADS_FOLDER, package_name)

            self._manager.silence_scheduler()

            install_message = INSTALLING_GATE1 + package_name + INSTALLING_GATE2
            self.print_progress(install_message, strings.UPLOAD_PROGRESS)
            py_install.install_package(package_name, package_path)

            self._manager.resume_scheduler()

            # Clean up
            if not self._clean_up('gate'):
                kwargs['continue_complex_upload'] = False

            kwargs['break'] = True

        return kwargs

    @parse_upload_folders
    def _reset_bridge(self, **kwargs):
        """ Request bridge reset to network defaults (if AES is set) """
        LOGGER.debug('_reset_bridge')

        if kwargs['dir_name'] == 'database':
            # Request bridge reset to network defaults (if needed)
            reset_needed = self._manager.reset_network()

            LOGGER.debug('reset_needed: ' + str(reset_needed))

            if reset_needed:
                # Print reset message
                self.print_progress(RESETTING_BRIDGE, strings.UPLOAD_PROGRESS)

                # Add bridge to post targets (so we wait until reset is done)
                del self._targets[:]
                self._post_targets.append(self._manager.bridge.base)

                # Force system to wait till bridge reset is done
                kwargs['continue_complex_upload'] = False

            kwargs['break'] = True

        return kwargs

    def _request_reboot_ack(self):
        """ Requesting reboot ack from user """
        continue_complex_upload = True
        LOGGER.debug('_request_reboot_ack')

        # Set some flags
        self._manager.reboot_flag = True
        self._reboot_ack = False

        # Notify user
        if platforms.PLATFORM in platforms.EMBEDDED_PLATFORMS:
            action_required = strings.REBOOT_REQUIRED
        else:
            action_required = strings.RESTART_REQUIRED

        self.finish_upload(UPLOAD_SUCCESS + ' ' + action_required, True)

        return continue_complex_upload

    def _wait_for_reboot_ack(self):
        """ Waiting on reboot ack """
        continue_complex_upload = self._reboot_ack
        LOGGER.debug('_wait_for_reboot_ack')

        if self._reboot_ack:
            # Halt scheduler
            self._manager.silence_scheduler()

        return continue_complex_upload

    @parse_upload_folders
    def _delete_logs(self, **kwargs):
        """ Delete Logs (if needed) """
        LOGGER.debug('_delete_logs')

        if kwargs['dir_name'] == 'logs':
            if file_system.empty_dir(common.LOGS_FOLDER):
                # Clean up
                if not self._clean_up('logs'):
                    kwargs['continue_complex_upload'] = False

            else:
                kwargs['continue_complex_upload'] = False

            kwargs['break'] = True

        return kwargs

    @parse_upload_folders
    def _update_gate_time(self, **kwargs):
        """ Updates E10 UTC Time (if needed) """
        LOGGER.debug('_update_gate_time')

        if kwargs['dir_name'] == 'database':
            if platforms.PLATFORM in platforms.EMBEDDED_PLATFORMS:
                # Update E10 UTC time #
                # Prepare time to appropriate format
                change_time_str = self._manager.system_settings.set_linux_time()

                # Set time
                self._manager.websocket.send(change_time_str)
                os.system(change_time_str)

            kwargs['break'] = True

        return kwargs

    @parse_upload_folders
    def _delete_database(self, **kwargs):
        """ Delete Database (if needed) """
        LOGGER.debug('_delete_database')

        if kwargs['dir_name'] == 'database':
            if file_system.empty_dir(common.DATABASE_FOLDER):
                # Clean Up #
                if not self._clean_up('database'):
                    kwargs['continue_complex_upload'] = False

            else:
                self.finish_upload(FILE_ERROR, False)
                kwargs['continue_complex_upload'] = False

            kwargs['break'] = True

        return kwargs

    @parse_upload_folders
    def _clean_up(self, directory, **kwargs):
        """
        Deletes folders from the unpacked archive.
        This also signals that particular update routine was already executed.
        """
        kwargs['continue_complex_upload'] = False
        if kwargs['dir_name'] == directory:
            LOGGER.debug("Clean Up: " + kwargs['zip_dir'])
            kwargs['continue_complex_upload'] = os.path.isdir(kwargs['zip_dir'])
            file_system.remove_dir(kwargs['zip_dir'])
            kwargs['break'] = True

        return kwargs

    ## Upload Triggers ##
    def check_upload(self, check_type):
        """ Overloading method so we can implement cancel gate upload functionality """
        if self.update_in_progress('gate') and self.cancel_complex_upload:
            self.complex_upload()

        else:
            super(ComplexUploader, self).check_upload(check_type)

    ## Callback Methods ##
    def snap_upload_callback(self, status_code):
        """ Report the final result to the user """
        success = bool(status_code == SUCCESS)
        callback_message = CALLBACK_MESSAGES.get(status_code, UPLOAD_UNKNOWN)

        # Perform following procedures on success
        if success:
            # Clean Up
            self.delete_target()

            # Report
            if len(self._post_targets):
                callback_message += ' ' + RESETTING_NODE

            self.print_progress(callback_message)

            # Continue
            if len(self._targets):
                LOGGER.debug('Next simple upload')
                self.simple_upload()

            elif not len(self._post_targets):
                if self.update_in_progress('gate'):
                    LOGGER.debug('Continue with complex upload')
                    self.complex_upload()

                else:
                    LOGGER.debug('Finish Upload on success')
                    self.finish_upload(callback_message, success)

        else:
            LOGGER.debug('Finish Upload on failure')
            self.finish_upload(callback_message, success)

    ## Internal Methods ##
    def print_progress(self, append_message='', _progress_message=None, _progress_percentage=None):
        """ Displays appropriate progress message depending on upload type """
        if self.update_in_progress('gate'):
            if len(self._targets):
                node = self._targets[0]

                # Figure out Progress Percentage
                if node['type'] == 'node' and '_index' in node:
                    current_node = node['_index']
                    if UPLOAD_SUCCESS in append_message:
                        current_node += 1

                    _progress_percentage = ((self._current_step + (float(current_node) / float(self._total_nodes))) *
                                            100.0) / self._total_steps

            if _progress_percentage is None and self._total_steps != 0.0:
                _progress_percentage = (self._current_step / self._total_steps) * 100.0

        super(ComplexUploader, self).print_progress(append_message, _progress_message, _progress_percentage)

    def delete_target(self):
        """
        Deletes folders from the unpacked archive.
        This also signals that particular update routine was already executed.
        """
        super(ComplexUploader, self).delete_target()

        if self.update_in_progress('gate'):
            if len(self._post_targets):
                for field in ('_index', '_path'):
                    target = self._post_targets[0]
                    if field in target:
                        del target[field]

            if not len(self._targets) and len(self._post_targets):
                target = self._post_targets[0]
                self._clean_up(target['type'])

    def finish_upload(self, finish_message, success):
        """
        Finishes(Aborts) software upload and sends appropriate message
        success: True or False. Indicates if its a success or abort message
        """
        if self.update_in_progress('gate'):
            if not success:
                file_system.empty_dir(common.UPLOADS_FOLDER)

            self.cancel_complex_upload = False

        super(ComplexUploader, self).finish_upload(finish_message, success)
