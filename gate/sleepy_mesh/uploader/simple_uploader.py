"""
Simple Uploader Class, handles node, base, virgin uploads
"""

### INCLUDES ###
import os
import logging

from distutils.version import StrictVersion

from gate import strings
from gate.conversions import find_version

from .snap_uploader import SnapUploader, SUCCESS, CANCEL


### CONSTANTS ###
FORCE_NODE_UPLOAD = False
# RESUME_DELAY = 1.0          # seconds

# Software Update Constants #
SOFTWARE_UPDATE_INFO = {
    'node': ('node', ['.spy']),
    'virgin': ('node', ['.spy']),
    'base': ('base', ['.spy']),
    'gate': ('gate', ['.zip', '.vol', '.pea'])
}

## Strings ##
UPLOAD_WAITING = "Waiting for appropriate timing!"
NODE_UP_TO_DATE = "is up to date and does not require software update!"

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class SimpleUploader(SnapUploader):
    def __init__(self, manager):
        super(SimpleUploader, self).__init__(manager)

        # Upload Interface #
        self._update_interface = self._manager.update_interfaces.create(SOFTWARE_UPDATE_INFO.keys())
        self.update_in_progress = self._update_interface.update_type

        # Upload targets and post processing targets lists
        self._targets = list()
        self._post_targets = list()

        # Lock so we do not execute the same update process multiple times
        self._upload_lock = False

        # Progress related members
        self._total_nodes = 0

    ## Simple Upload Methods ##
    def simple_upload(self, file_path=None):
        """ Internal Function to assign upload info for the simple upload """
        LOGGER.debug('Simple Upload')

        # Init simple upload
        if file_path is not None:
            if len(self._targets):
                self._total_nodes = len(self._targets)

                for target_index, target in enumerate(self._targets):
                    target['_index'] = target_index
                    target['_path'] = file_path

        # Restart scheduler (if needed)
        self._manager.resume_scheduler(False, complete_callback=self.__start_simple_upload)

    ## Upload Triggers ##
    def check_upload(self, check_type):
        """ Start software upload of particular type if target queue is not empty """
        software_upload_in_progress = False
        # LOGGER.debug('check_type: ' + str(check_type))
        # LOGGER.debug('len(self._targets): ' + str(len(self._targets)))
        # LOGGER.debug('len(self._post_targets): ' + str(len(self._post_targets)))

        if len(self._targets):
            if self._targets[0]['type'] == check_type:
                # LOGGER.debug("_targets[0]['type'] = " + self._targets[0]['type'])
                # LOGGER.debug("self._upload_lock = " + str(self._upload_lock))
                if not self._upload_lock:
                    self._upload_lock = True
                    if self._targets[0]['type'] != 'gate':
                        self._manager.stop_scheduler()
                        self.print_progress()
                        self.start_snap_upload(self._targets[0])

                        software_upload_in_progress = True
                    else:
                        self.finish_upload(strings.UNKNOWN_ERROR, False)

        elif len(self._post_targets):
            if check_type in ('node', '_node'):
                for target_index, target in enumerate(self._post_targets):
                    if target['type'] == 'node':
                        if not target['post_software_update']:
                            del self._post_targets[target_index]
                            break

        elif self.update_in_progress():
            if self.cancel_snap_upload:
                self.snap_upload_callback(CANCEL)

            elif check_type in ('node', '_node', 'base'):
                self.snap_upload_callback(SUCCESS)

        return software_upload_in_progress

    ## Callback Methods ##
    def base_reboot_callback(self, *args):
        """ Reboot confirmation triggered by Base node """
        if len(self._post_targets):
            if self._post_targets[0]['type'] == 'base':
                self.print_progress(strings.BASE_REBOOT_COMPLETED)
                del self._post_targets[0]

                self.snap_upload_callback(SUCCESS)

    ## Internal Methods ##
    def print_progress(self, append_message='', _progress_message=None, _progress_percentage=None):
        """ Displays appropriate progress message depending on upload type """
        # Figure out Progress Message
        if _progress_message is None:
            _progress_message = strings.UPLOAD_PROGRESS
            if len(self._targets):
                node = self._targets[0]
                if node['type'] == 'node' and '_index' in node:
                    _progress_message = strings.UPLOAD_NODE1 + str(node['name'])
                    _progress_message += strings.UPLOAD_NODE2 + str(node['_index'] + 1)
                    _progress_message += strings.UPLOAD_NODE3 + str(self._total_nodes)
                    _progress_message += strings.UPLOAD_NODE4

                elif node['type'] == 'base':
                    _progress_message = strings.UPLOAD_BASE

        self._manager.websocket.send(_progress_message, 'ws_init', _progress_percentage)
        if len(append_message):
            self._manager.websocket.send(append_message, 'ws_append', _progress_percentage)

    def delete_target(self):
        """ Deletes targets """
        if len(self._targets):
            target = self._targets[0]

            # Clean up nodes #
            if target['type'] in ('node', 'base', 'virgin'):
                if target['type'] in ('node', 'base'):
                    target['software_update'] = False
                    self._manager.resume_scheduler(False)

                    if target['type'] == 'base':
                        self._manager.bridge.request_base_node_reboot()

                elif target['type'] == 'virgin':
                    self._manager.bridge.network_ucast(target['net_addr'], 'reboot')
                    # Delete virgin - should appear as normal node after reboot
                    target.delete()
                    self._manager.platforms.delete_node(target)

                if target['type'] in ('node', 'base'):
                    self._post_targets.append(self._targets.pop(0))

                else:
                    del self._targets[0]

    def finish_upload(self, finish_message, success):
        """
        Finishes(Aborts) software upload and sends appropriate message
        success: True or False. Indicates if its a success or abort message
        """
        del self._targets[:]

        self._upload_lock = False
        self.cancel_snap_upload = False

        self._update_interface.finish_update(finish_message)

        # Restart scheduler
        self._manager.resume_scheduler(True)
        # self._manager.bridge.schedule(RESUME_DELAY, self._manager.resume_scheduler)

    ## Class-Private Methods ##
    def __start_simple_upload(self):
        """ Starts simple upload """
        self._upload_lock = False
        self.cancel_snap_upload = False

        self.print_progress(UPLOAD_WAITING)

        if len(self._targets):
            software_update_needed = self.__software_update(self._targets[0])
            self._targets[0]['software_update'] = software_update_needed
            self._targets[0]['post_software_update'] = software_update_needed
            if not software_update_needed:
                self.snap_upload_callback(SUCCESS)

        else:
            self.snap_upload_callback(SUCCESS)

    def __software_update(self, target):
        """ Determine if software update needed on this particular node """
        output = True
        if not FORCE_NODE_UPLOAD:
            update_file_name = os.path.splitext(os.path.basename(target['_path']))[0]
            # LOGGER.debug('update_file_name: ' + str(update_file_name))
            present_version = StrictVersion(find_version(target['software']))
            # LOGGER.debug('present_version: ' + str(present_version))
            update_version = StrictVersion(find_version(update_file_name))
            # LOGGER.debug('update_version: ' + str(update_version))
            output = bool(update_version > present_version)
            # LOGGER.debug('software_update: ' + str(software_update))

            if not output:
                up_to_date_message = strings.FIELD_UNIT + " '" + target['name']
                up_to_date_message += "' " + NODE_UP_TO_DATE
                self.print_progress(up_to_date_message)

        return output
