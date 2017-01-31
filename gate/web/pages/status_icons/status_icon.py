"""
Status Icon Class
"""

### INCLUDES ###
import logging

from bottle import template

from gate.conversions import internal_name


### CONSTANTS ###
## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.ERROR)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class StatusIcon(object):
    def __init__(self, title, modes=None, enable_legend=True):
        self.internal_name = internal_name(title)
        self.title = title
        self.modes = modes
        self.enable_legend = enable_legend and (self.modes is not None)

        self.pop_up_enable = False
        self.sound_enable = False

    def header_html(self, current_mode=None):
        """ Returns html that we plug into header """
        if self.modes is None:
            current_mode = ''

        if current_mode is None or current_mode not in self.modes.keys():
                current_mode = self.modes.keys()[0]

        if len(current_mode):
            current_mode = '_' + current_mode

        output = "<input id='" + self.internal_name + "_icon' type='image' "
        output += "src='/img/" + self.internal_name + current_mode + ".png' "
        if len(self.status_message()) or self.enable_legend:
            output += "onclick=\"Overlay('" + self.internal_name + "')\" "
        output += "alt='" + self.title + "' title='" + self.title + "' width='25' height='25' >"

        return output

    def overlay(self):
        """ Returns Overlay html """
        output = "<div id='" + self.internal_name + "_overlay' class='hidden'>"

        output += "<div id='" + self.internal_name + "_message'>"
        output += self.status_message()
        output += "</div>"

        output += "<div id='" + self.internal_name + "_legend'>"
        output += self.legend()
        output += "</div>"

        output += "<input type='button' value='Okay' onclick='Overlay(false)' >"
        output += "</div>"

        return output

    def legend(self):
        """ Returns icon legend """
        output = ''
        if self.enable_legend:
            output = template('legend', status_icon=self)

        return output

    ## Overloading Methods ##
    def status_message(self):
        """ Returns Status Message """
        return ''

    def current_icon(self, current_mode_key=None):
        """ Provides link to current icon """
        current_mode = ''

        if self.modes is not None:
            current_mode = self.modes.keys()[0]

            if current_mode_key is not None:
                if type(current_mode_key) in (int, long, float):
                    if current_mode_key >= len(self.modes):
                        self.pop_up_enable = True
                        current_mode = self.modes.keys()[-1]

                    else:
                        self.pop_up_enable = False
                        if 0 <= current_mode_key < len(self.modes):
                            current_mode = self.modes.keys()[current_mode_key]

                elif type(current_mode_key) in (str, unicode):
                    if current_mode_key in self.modes.keys():
                        current_mode = current_mode_key

            self.sound_enable = current_mode in ('active', ) and self.internal_name in ('warnings', )

        if len(current_mode):
            current_mode = '_' + current_mode

        return '/img/' + self.internal_name + current_mode + '.png'

    def json_dict(self):
        """ Compiles JSON dict for the icon to do ajax updates """
        json_dict = dict()

        _status_message = self.status_message()
        if len(_status_message) or self.internal_name in ('warnings', ):
            json_dict['status_message'] = _status_message

        if self.modes is not None and self.internal_name not in ('system_status', ):
            json_dict['current_icon'] = self.current_icon()

        if 'current_icon' in json_dict:
            json_dict['pop_up_enable'] = int(self.pop_up_enable)
            json_dict['sound_enable'] = int(self.sound_enable)

        json_dict['onclick_enable'] = int(len(_status_message) or self.enable_legend)

        return json_dict
