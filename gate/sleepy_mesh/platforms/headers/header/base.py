"""
Header Base Class
"""

### INCLUDES ###
import os
import logging

from gate.database import DatabaseDict
from gate.conversions import internal_name
from gate.sleepy_mesh.node.data import DISPLAY_FIELDS


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class HeaderBase(DatabaseDict):
    """
    Header Base Class.
    This class is used as a common base class for other header data type classes such as
    header constant, variable and unit classes.
    """

    def __init__(self, name, data_field, platform, header_name, header_position, **kwargs):
        """ Initializes base class for all header type instances. Following parameters are must haves across all
            header type instances

        :param name: Official name that might be displayed to user via web interface. This also used to
            generate internal constant name that is used internally.
        :param data_field: Raw data field that this constant is associated to.
            This gets automatically filled in by Header class.
        :param platform:
        :param header_position:
        :param kwargs:
        :return: Initialized base class
        """
        _internal_name = internal_name(name)

        data_field_position = None
        if data_field in DISPLAY_FIELDS:
            data_field_position = DISPLAY_FIELDS.index(data_field)

        db_file = os.path.join('headers', platform, _internal_name + '.db')

        defaults = {
            # Global Must Haves
            'name': name,
            'internal_name': _internal_name,
            'data_field': data_field,
            'data_field_position': data_field_position,
            'platform': platform,
            'header_name': header_name,
            'header_position': header_position,
            '_external': False
        }
        defaults.update(kwargs)

        super(HeaderBase, self).__init__(
            db_file=db_file,
            defaults=defaults
        )

    ## Enable Related ##
    def enables(self, provider, enable_type, set_value=None):
        """
        Either get or sets particular enable value

        :param provider: data provider that we are working with
        :param enable_type: choose between ``live_enable``, ``log_enable`` or ``const_set``
        :param set_value: provide None if reading, provide write value if writing
        :return: either read value or write value of the enable
        """
        output = None

        if enable_type in ('live_enable', 'log_enable', 'const_set'):
            # Write
            if set_value is not None:
                provider['enables'][self['header_position']][enable_type] = bool(set_value)
            # Read
            output = provider['enables'][self['header_position']][enable_type]

            # Debugging
            # if set_value is not None and 'net_addr' in provider:
            #     debug_str = "nodes[" + provider['net_addr'] + "]['enables']["
            #     debug_str += str(self['header_position']) + "][" + str(enable_type) + "]: "
            #     debug_str += str(provider['enables'][self['header_position']][enable_type])
            #     LOGGER.debug(debug_str)

        else:
            LOGGER.error("Enable type: " + str(enable_type) + " does not exist!")

        return output

    ## Alarm Related ##
    def alarm_enable(self, provider, alarm_type, new_value=None):
        """
        Either get or sets particular alarm enable

        :param provider: data provider that we are working with
        :param alarm_type: choose between ``min_alarm`` or ``max_alarm``
        :param new_value: provide None if reading, provide write value if writing
        :return: either read value or write value of the enable
        """
        if self['_external']:
            return self._alarm(provider, alarm_type, '_enable', new_value)

        else:
            return bool(self[alarm_type] is not None)

    def alarm_value(self, provider, alarm_type, new_value=None):
        """
        Either get or sets particular alarm threshold value

        :param provider: data provider that we are working with
        :param alarm_type: choose between ``min_alarm`` or ``max_alarm``
        :param new_value: provide None if reading, provide write value if writing
        :return: either read value or write value of the alarm
        """
        if self['_external']:
            return self._alarm(provider, alarm_type, '_value', new_value)

        else:
            return self[alarm_type]

    def _alarm(self, provider, alarm_type, alarm_register, new_value=None):
        """
        Either get or sets particular alarm threshold value or enable

        :param provider: data provider that we are working with
        :param alarm_type: choose between ``min_alarm`` or ``max_alarm``
        :param new_value: provide None if reading, provide write value if writing
        :param alarm_register: Specify either ``_enable`` or ``_value`` register
        :return: either read value(or enable) or write value(or enable) of an alarm
        """
        output = None

        if alarm_type in ('min_alarm', 'max_alarm'):
            if alarm_register in ('_enable', '_value'):
                # Write
                if new_value is not None:
                    if alarm_register == '_enable':
                        new_value = bool(new_value)
                    provider['alarms'][self['header_position']][alarm_type + alarm_register] = new_value
                # Read
                output = provider['alarms'][self['header_position']][alarm_type + alarm_register]
            else:
                LOGGER.error("Alarm register: " + str(alarm_register) + " does not exist!")
        else:
            LOGGER.error("Alarm type: " + str(alarm_type) + " does not exist!")

        return output

    def check_alarm(self, provider, calculated_value, alarm_type):
        """
        Checks if any alarms or sensor circuitry faults has been triggered
        Alternatively clear alarms
        :return: NA
        """
        output = False

        alarm_enable = self.alarm_enable(provider, alarm_type)
        if alarm_enable:
            # Check and Set Alarm
            alarm_value = self.alarm_value(provider, alarm_type)
            if type(alarm_value) in (float, int) and type(calculated_value) in (float, int):
                if alarm_type == 'min_alarm':
                    # Min Alarm Check
                    output = bool(calculated_value < alarm_value)
                elif alarm_type == 'max_alarm':
                    # Max Alarm Check
                    output = bool(calculated_value > alarm_value)

        return output

    def alarm_message(self, alarm_type):
        """ Fetch alarm messages for this particular header """
        output = None
        if self[alarm_type + '_message']:
            if self['_external']:
                output = self['header_name']
            else:
                output = self['name']

            output += self[alarm_type + '_message']

        return output
