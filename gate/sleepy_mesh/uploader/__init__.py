"""
Uploader Interface
"""

### INCLUDES ###
import os
# import re
import logging

from bottle import request
from py_knife import file_system, upload

from gate import strings, common

from .simple_uploader import SOFTWARE_UPDATE_INFO
from .complex_uploader import ComplexUploader


### CONSTANTS ###
## Delays ##
UPLOAD_DELAY = 3.0          # seconds

## Strings ##
SIMPLE_UPLOAD_CANCEL = "Cancelling software upload!"
COMPLEX_UPLOAD_CANCEL1 = "Finishing up current procedure before cancelling software update!"
COMPLEX_UPLOAD_CANCEL2 = COMPLEX_UPLOAD_CANCEL1
COMPLEX_UPLOAD_CANCEL2 += " Press cancel button again if you would like to cancel current procedure!"

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.ERROR)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class Uploader(ComplexUploader):
    """ Hacked portion of the uploader """
    def __init__(self, manager):
        super(Uploader, self).__init__(manager)

    ## Edit Methods ##
    def init_upload(self, upload_type, targets):
        """ Upload file from the user and updates node's (virgin's) software """
        return_dict = {'kwargs': {}}

        # Make sure user made file selection
        if not request.files.data:
            return_dict['kwargs']['alert'] = strings.NO_FILE

        # Get data from form
        else:
            LOGGER.debug("upload_type = " + upload_type)

            # Split filename
            data = request.files.data

            filename, extension = os.path.splitext(data.filename.lower())

            # For future use
            # filename_list = re.split('-|_', filename)
            # if len(filename_list) > 1:
            #     version = filename_list[-1]
            # else:
            #     version = "undefined"

            LOGGER.debug("Filename: " + str(filename))
            # LOGGER.debug("Version: " + version)
            LOGGER.debug("Extension: " + extension)

            if targets is None:
                return_dict['kwargs']['alert'] = strings.NO_NODE

            upload_types = SOFTWARE_UPDATE_INFO.keys()
            if upload_type not in upload_types:
                return_dict['kwargs']['alert'] = strings.UNKNOWN_ERROR

            else:
                valid_filename = SOFTWARE_UPDATE_INFO[upload_type][0]
                valid_extensions = SOFTWARE_UPDATE_INFO[upload_type][1]
                if valid_filename not in filename:
                    # Cancel and display alert
                    return_dict['kwargs']['alert'] = strings.WRONG_FILENAME
                elif extension not in valid_extensions:
                    # Cancel and display alert
                    return_dict['kwargs']['alert'] = strings.WRONG_EXTENSION
                else:

                    if not self.update_in_progress():
                        self._manager.websocket.send(strings.UPLOAD_SAVING, 'ws_init')

                        # TODO: Move scheduler delay to HERE (or make it into a thread!)
                        file_system.empty_dir(common.UPLOADS_FOLDER)
                        file_path = upload.save_upload(common.UPLOADS_FOLDER, data)

                        if not file_path:
                            return_dict['kwargs']['alert'] = strings.UNKNOWN_ERROR
                        else:
                            self._update_interface.start_update(upload_type)
                            self._manager.silence_scheduler()

                            if type(targets) not in (list, tuple):
                                targets = [targets]

                            self._targets = targets

                            if self.update_in_progress('gate'):
                                self._manager.websocket.send(strings.UPLOAD_UNPACKING, 'ws_init', 0.0)
                                upload_method = self.complex_upload
                            else:
                                upload_method = self.simple_upload

                            self._manager.bridge.schedule(UPLOAD_DELAY, upload_method, file_path)

                    else:
                        LOGGER.warning("Client's browser tried to execute " + str(upload_type) + " multiple times!")

        return return_dict

    ## Cancel Upload Methods ##
    def request_cancel_upload(self):
        """ Cancels Software Upload """
        gate_update = self.update_in_progress('gate')
        if gate_update and self.cancel_complex_upload:
            # Takes double cancel during gate update to start canceling internal simple upload
            self.cancel_snap_upload = True

        elif gate_update:
            # Complex update cancel
            self.cancel_complex_upload = True

        else:
            # Simple upload cancel
            self.cancel_snap_upload = True

        if self.cancel_snap_upload:
            if len(self._targets):
                self._manager.websocket.send(SIMPLE_UPLOAD_CANCEL, 'ws_init')
        elif self.cancel_complex_upload:
            if len(self._targets):
                self._manager.websocket.send(COMPLEX_UPLOAD_CANCEL2, 'ws_init')
            else:
                self._manager.websocket.send(COMPLEX_UPLOAD_CANCEL1, 'ws_init')
