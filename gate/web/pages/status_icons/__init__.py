"""
Status Icons Class
"""

### INCLUDES ###
import copy
import logging

from bottle import template

from py_knife.ordered_dict import OrderedDict

from status_icon import StatusIcon

from ..base import PagesBase


### CONSTANTS ###
STATUS_ICONS = list()

## Icon Modes ##
DISPLAY_OPTIONS_MODES = OrderedDict()
DISPLAY_OPTIONS_MODES['none'] = 'Display Options Disabled'
DISPLAY_OPTIONS_MODES['active'] = 'Display Options Enabled'

LOG_EXPORT_MODES = OrderedDict()
LOG_EXPORT_MODES['none'] = 'Log Export Disabled'
LOG_EXPORT_MODES['active'] = 'Log Export Enabled'

WARNINGS_MODES = OrderedDict()
WARNINGS_MODES['none'] = 'No Warnings'
WARNINGS_MODES['acknowledged'] = 'Acknowledged Warnings'
WARNINGS_MODES['active'] = 'Active Warnings'

POWER_MODES = OrderedDict()
POWER_MODES['green'] = 'Best Battery Life (sleep time >= 60s)'
POWER_MODES['yellow'] = 'Medium Battery Life (30s <= sleep time < 60s)'
POWER_MODES['red'] = 'Reduced Battery Life (sleep time < 30s)'

SYSTEM_MODES = OrderedDict()
SYSTEM_MODES['offline'] = 'Mesh Network is Offline'
SYSTEM_MODES['sleep'] = 'Mesh Network is in Sleep Mode'
SYSTEM_MODES['awake'] = 'Mesh Network is in Awake Mode'
# SYSTEM_MODES['online'] = 'Mesh Network is Online'

## Logger ##
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.ERROR)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class StatusIcons(PagesBase):
    def __init__(self, **kwargs):
        super(StatusIcons, self).__init__(**kwargs)

        self._status_icons = OrderedDict()

        # Warnings Icon #
        # FIXME: More elegant way to do this?
        warnings_icon = StatusIcon('Warnings', WARNINGS_MODES)

        def _warnings_message():
            output = ''

            warnings = self.platforms.warnings()
            if len(warnings):
                output += template('warnings', warnings=warnings, status_icon=warnings_icon)
            return output

        warnings_icon.status_message = _warnings_message

        warnings_old_current_icon = warnings_icon.current_icon

        def _warnings_icon():
            warnings_state = self.platforms.warnings_state()
            LOGGER.debug('warnings_state: ' + str(warnings_state))
            return warnings_old_current_icon(warnings_state)

        warnings_icon.current_icon = _warnings_icon

        self._status_icons[warnings_icon.internal_name] = warnings_icon

        # Power Consumption Icon #
        power_consumption_icon = StatusIcon('Power Consumption', POWER_MODES)

        power_consumption_old_current_icon = power_consumption_icon.current_icon

        def _power_consumption_icon():
            power_consumption_state = self.manager.networks[0].power_consumption_state()
            return power_consumption_old_current_icon(power_consumption_state)

        power_consumption_icon.current_icon = _power_consumption_icon
        self._status_icons[power_consumption_icon.internal_name] = power_consumption_icon

        # System Status Icon #
        system_status_icon = StatusIcon('System Status', SYSTEM_MODES)
        self._status_icons[system_status_icon.internal_name] = system_status_icon

    ## Public Methods ##
    def header(self):
        """ Returns selected page header """
        output = ''

        # TODO: Move html to templates
        if self.users.check_access('user') and not self['login_page']['selected']:
            right_column_width = 15

            current_url = self.url()
            center_column_enable = bool(self.url('live_data') in current_url)

            if center_column_enable:
                left_column_width = right_column_width
            else:
                left_column_width = 100 - right_column_width

            output = "<table style='width: 100%;'><tr>"
            output += "<td style='width: " + str(left_column_width) + "%;text-align: left;'>"
            output += super(StatusIcons, self).header()
            output += "</td>"

            if center_column_enable:
                output += "<td style='text-align: center;font-size: 14px;'>"
                output += "<span id='page_controls'>"
                output += "</span></td>"

            output += "<td style='width: " + str(right_column_width) + "%;'>"
            output += "<span class='float_right'>"

            # New Shit #
            for status_icon in self.status_icons().values():
                output += status_icon.header_html()

            output += "</span></td>"
            output += "</tr></table>"

        else:
            output += super(StatusIcons, self).header()

        return output

    def status_icons_overlay(self):
        """ Fetch status icon overlay """
        output = ''
        for status_icon in self.status_icons().values():
            output += status_icon.overlay()

        return output

    def status_icons(self):
        """ Fetch Status Icons """
        output = copy.deepcopy(self._status_icons)

        insert_icon = None
        if len(self.platforms.select_nodes('active')):
            current_url = self.url()
            if self.url('live_data') in current_url:
                # Display Options Icon #
                display_options_icon = StatusIcon('Table Display Options', DISPLAY_OPTIONS_MODES, enable_legend=False)

                def _display_options_message():
                    _output = '<h3>' + display_options_icon.title + '</h3>'
                    group = self.get_group()
                    _output += template('table_units', group=group, page_type='live')
                    return _output

                display_options_icon.status_message = _display_options_message
                insert_icon = display_options_icon

            elif self.url('logs_data') in current_url:
                # Log Export Icon #
                log_export_icon = StatusIcon('Log Export', LOG_EXPORT_MODES, enable_legend=False)

                def _log_export_message():
                    group = self.get_group()
                    _output = self.template_html(None, 'log_export', group=group)
                    return _output

                log_export_icon.status_message = _log_export_message
                insert_icon = log_export_icon

        if insert_icon is not None:

            _old_current_icon = insert_icon.current_icon

            def _insert_icon_current_icon():
                active_nodes = self.platforms.select_nodes('active')
                active_state = int(bool(len(active_nodes)))
                return _old_current_icon(active_state)

            insert_icon.current_icon = _insert_icon_current_icon

            output.insert_before(output.keys()[0], (insert_icon.internal_name, insert_icon))

        return output

    ## Private Methods ##
    def _status_icons_json(self):
        """ Generates JSON dictionary to update status icons via AJAX """
        json_dict = dict()
        json_dict['status_icons'] = dict()

        for status_icon_key, status_icon in self.status_icons().items():
            json_dict['status_icons'][status_icon_key] = status_icon.json_dict()

        return json_dict
