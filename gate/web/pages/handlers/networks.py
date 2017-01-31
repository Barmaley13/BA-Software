"""
Networks Web Handler with integrated Edit Methods
"""

### INCLUDES ###
from bottle import request

# from gate.conversions import round_float, round_base_float
from gate.conversions import CYCLES_MAX_INT, TIMEOUT_MAX_FLOAT
from gate.strings import VALIDATION_FAIL

from gate.web.pages.handlers import WebHandlerBase


### CLASSES ###
class WebHandler(WebHandlerBase):
    def __init__(self, pages):
        super(WebHandler, self).__init__(pages, pages.manager.networks[0])

    def _restore(self, cookie):
        """ Restore indexed network to default """
        return_dict = {
            'kwargs': {},
            'validate': True
        }

        # Restore to defaults
        self._manager.reset_network(force_reset=True)

        return return_dict

    def _update_network(self, cookie):
        """ Updates indexed network """
        validate = True

        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        # Get data from forms
        # net_id = request.forms.net_id.encode('ascii', 'ignore')
        channel = int(request.forms.channel)
        data_rate = int(request.forms.data_rate)
        aes_key = request.forms.aes_key.encode('ascii', 'ignore')
        aes_enable = int(request.forms.aes_enable)
        wake = float(request.forms.wake)
        sleep = float(request.forms.sleep)
        timeout_wake = float(request.forms.timeout_wake)
        timeout_sleep = float(request.forms.timeout_sleep)

        # # Round just in case
        # wake = round_base_float(wake)
        # sleep = round_base_float(sleep)
        # timeout_wake = round_float(timeout_wake)
        # timeout_sleep = round_float(timeout_sleep)

        # # Validate data
        # # Make sure net_id is 4 bytes long and has valid digits
        # validate &= all(char in string.hexdigits for char in net_id) and (len(net_id) == 4)

        # Make sure aes_key is 16 bytes long if enabled
        if aes_enable == 1:
            validate &= (len(aes_key) <= 16)
        # Make sure those are in the right range
        for value in (wake, sleep):
            validate &= (0 < value <= CYCLES_MAX_INT)

        validate &= sleep + wake/2 <= CYCLES_MAX_INT

        for value in (timeout_wake, timeout_sleep):
            validate &= (0 < value <= TIMEOUT_MAX_FLOAT)

        if validate:
            # Create save dictionary
            save_dict = {
                'channel': channel,
                'data_rate': data_rate,
                'aes_key': aes_key.ljust(16),
                'aes_enable': aes_enable,
                'wake': wake,
                'sleep': sleep,
                'timeout_wake': timeout_wake,
                'timeout_sleep': timeout_sleep
            }
            if aes_enable == 0:
                del save_dict['aes_key']
            # Load local buffers with save dictionary
            self._manager.request_update(save_dict)

            self._object.save()
        else:
            return_dict['kwargs']['alert'] = VALIDATION_FAIL

        return return_dict

    def _save_software(self, cookie):
        """ Just a buffer """
        return self._manager.uploader.init_upload('base', self._manager.bridge.base)
