"""
Snap Uploader Class interfacing Snap Uploader
"""

### INCLUDES ###
import logging

from snaplib import ScriptsManager
from snaplib import SnappyUploader

from gate.conversions import hex_to_bin


### CONSTANTS ###
# Snap Uploader Constants #
# Time to wait for a remote device to respond to upload requests
WAIT_TIME = 60
# Number of programming retries
UPLOAD_RETRIES = 3

## Status Messages ##
NO_INSTANCE = -1        # No SNAP Connect instance
NO_SUCH_FILE = -2       # SPY file that does not exist
TOO_MANY_RETRIES = -3   # Maximum number of upload attempts exceeded
CANCEL = SnappyUploader.SNAPPY_PROGRESS_CANCELED
TIMEOUT = SnappyUploader.SNAPPY_PROGRESS_TIMEOUT
SUCCESS = SnappyUploader.SNAPPY_PROGRESS_COMPLETE

## Status Strings ##
UPLOAD_NO_FILE = "Software Upload could not upload file to the server!"
UPLOAD_MAX_RETRIES = "Software Upload failed after too many retries!"
UPLOAD_TIMEOUT = "Software Upload failed due to timeout!"
UPLOAD_SUCCESS = "Software has been updated successfully!"
UPLOAD_CANCELLED = "Software update has been cancelled!"
UPLOAD_UNKNOWN = "Status of the Software Update is unknown!"

## Callback Messages ##
CALLBACK_MESSAGES = {
    NO_SUCH_FILE: UPLOAD_NO_FILE,
    TOO_MANY_RETRIES: UPLOAD_MAX_RETRIES,
    CANCEL: UPLOAD_CANCELLED,
    TIMEOUT: UPLOAD_TIMEOUT,
    SUCCESS: UPLOAD_SUCCESS
}

## Strings ##
PROGRESS_TICKS = " . . "

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class SnapUploader(object):
    """ Created using Snap Uploader Class Example (slightly hacked) """
    def __init__(self, manager):
        self._manager = manager

        # True WHILE a file upload is in progress
        self._upload_in_progress = False
        self._snap_uploader = None

        # Timer used to tell if commands are taking
        # too long (during the programming process)
        self._resp_timer = 0
        # Flag that keeps the timer tick from rescheduling itself
        self._stop_timer = False

        # Track the number of retries
        self._retry_flag = False

        # Upload target
        self._target = None

        # Cancel Update #
        self.cancel_snap_upload = False

    ## Default Uploader Methods ##
    def start_snap_upload(self, target):
        """ Function to begin the upload process """
        file_instance = None
        upload_image = None
        self._target = target
        self._target['_retries'] = 0
        # Just in case
        self._manager.bridge.set_vm_stat_callback(None)

        try:
            file_instance = open(self._target['_path'], 'rb')
            upload_image = ScriptsManager.getSnappyStringFromExport(file_instance.read())
        except:
            self._complete_process(NO_SUCH_FILE)
        finally:
            if file_instance is not None:
                file_instance.close()

        # Kickoff upload
        if upload_image:
            if not self._retry_flag:
                # Setup the timer tick
                self._manager.bridge.schedule(1.0, self._timer_tick)
            self._resp_timer = WAIT_TIME

            net_addr = hex_to_bin(self._target['net_addr'])
            self._snap_uploader = self._manager.bridge.com.spy_upload_mgr.startUpload(net_addr, upload_image)
            self._snap_uploader.registerFinishedCallback(self._app_upload_hook)
            self._upload_in_progress = True

    def _app_upload_hook(self, *args):
        """ Assigning callback of some sort """
        # snappy_upload_obj = args[0]
        result = args[1]
        self._complete_process(result)

    def _complete_process(self, err_code):
        """
        Process has completed (either in failure or success)
        Reset for the next time
        """
        # Keep the next timer tick from rescheduling itself
        self._stop_timer = True
        self._upload_in_progress = False
        self._retry_flag = False
        # Timer used to tell if commands are taking too long
        self._resp_timer = 0

        # Clean up #
        if '_retries' in self._target:
            del self._target['_retries']
        self._target = None

        self.snap_upload_callback(err_code)

    def _timer_tick(self):
        """
        Function called by timing mechanism on a regular basis
        Keeps track of when retries are needed
        """
        if self._upload_in_progress:
            if self.cancel_snap_upload:
                # User Cancelled - End things here
                self._snap_uploader.cancel()

            else:
                self._resp_timer -= 1
                self._manager.websocket.send(PROGRESS_TICKS, 'ws_append')
                if self._resp_timer == 0:
                    self._resp_timer = WAIT_TIME
                    self._target['_retries'] += 1
                    if self._target['_retries'] < UPLOAD_RETRIES:
                        self.start_snap_upload(self._target)
                    else:
                        # Too many retries - End things here
                        self._complete_process(TOO_MANY_RETRIES)

        if self._stop_timer:  # The way to stop the timer if necessary
            self._stop_timer = False
            return False

        return True  # Reschedule yourself

    ## Callback Methods ##
    def snap_upload_callback(self, status_code):
        LOGGER.error("Method upload_callback is not implemented!")
        raise NotImplementedError
