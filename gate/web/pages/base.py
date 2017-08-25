"""
Pages Base Class
"""

### INCLUDES ###
import os
import pkgutil
import logging

from bottle import template

from py_knife.ordered_dict import OrderedDict

from gate.database import DatabaseOrderedDict
from gate.web.users import Users, GUEST_USER

from . import handlers
from .platforms import WebPlatforms


### CONSTANTS ###
NAV_DEPTH = 1

## Strings ##
ACCESS_DENIED = "Access Denied for this user! Please contact your System Administrator!"
LOG_OUT = "Log Out"

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def init_pages(pages):
    """
    :param pages:
    :return:
    """
    for page in pages.values():
        init_page(page)


def init_page(page_dict):
    """
    Initializes Page variables including sub pages

    :param page_dict:
    :return: NA
    """
    page_dict['selected'] = False
    if 'template' not in page_dict:
        page_dict['template'] = os.path.join(*page_dict['url'].split('/'))

    if 'header' not in page_dict:
        page_dict['header'] = page_dict['title']

    if 'cookies' not in page_dict:
        page_dict['cookies'] = dict()

    if 'sub_pages' in page_dict:
        init_pages(page_dict['sub_pages'])

    if 'page_access' not in page_dict:
        page_dict['page_access'] = 'read'

    if 'get_handler' not in page_dict:
        page_dict['get_handler'] = (None, 'read')

    if 'post_handler' not in page_dict:
        page_dict['post_handler'] = None


def _midfix(field):
    """ Returns appropriate midfix """
    midfix = ''
    if field == 'url':
        midfix = '/'
    elif field == 'template':
        midfix = os.sep
    elif field == 'title' or field == 'header':
        midfix = ' - '
    return midfix


### CLASSES ###
class PagesBase(DatabaseOrderedDict):
    def __init__(self, manager):
        super(PagesBase, self).__init__()
        self.manager = manager
        self.platforms = WebPlatforms(self.manager)

        users_callbacks = {
            'update_user_panel': self.__update_user_panel,
            'select_user_panel': self.__select_user_panel
        }

        self.users = Users(users_callbacks, self.manager.system_settings)

        ## Web Handler Init ##
        self.handlers = dict()
        handlers_path = os.path.dirname(handlers.__file__)
        for importer, handler_module_name, is_package in pkgutil.iter_modules([handlers_path]):
            # LOGGER.debug("Found Handler %s (is a package: %s)" % (handler_module_name, is_package))
            if not is_package:
                handler_name = handler_module_name.split('.')[-1]
                if not handler_name.startswith('_'):
                    handler_module = importer.find_module(handler_module_name).load_module(handler_module_name)
                    self.handlers[handler_name] = handler_module.WebHandler(self)

        # LOGGER.debug('Handlers: ' + str(self.handlers))

        ## Default Pages ##
        # TODO: Change static page creation to dynamic page creation.
        # Might have to define page properties inside of each individual template.
        # Not quite sure how to implement such a functionality at this point
        # Main Pages #
        # Important: Main pages must not have access set to 'no_access'
        # meaning users that have 'no_access' can not access those pages
        # Note: title plays role of html title as well as button name in navigation
        live_cookies = self.platforms.default_cookie('live')
        log_cookies = self.platforms.default_cookie('log')
        # LOGGER.debug('live_cookies = ' + str(live_cookies))
        # LOGGER.debug('log_cookies = ' + str(log_cookies))

        self['live_data'] = {
            'url': 'live',
            'title': 'Live',
            'header': '',
            'cookies': live_cookies
        }
        self['logs_data'] = {
            'url': 'logs',
            'title': 'Logs',
            'header': '',
            'cookies': log_cookies,
            'post_handler': (self.handlers['platforms'], 'read')
        }
        self['setup_page'] = {
            'url': 'setup',
            'title': 'Setup',
            'sub_pages': OrderedDict()
        }
        self['diagnostics_page'] = {
            'url': 'diagnostics',
            'title': 'Diagnostics',
            'cookies': live_cookies
        }
        self['faq_page'] = {
            'url': 'faq',
            'title': 'FAQ',
            'header': 'Frequently Asked Questions',
            'page_access': 'user'
        }
        # Special Pages #
        # Important: Special pages must have access set to 'no_access',
        # meaning users that have 'no_access' can access those pages
        # Also, special pages have 'url' == ''
        self['login_page'] = {
            'url': 'login',
            'template': 'login',
            'title': 'Log In',
            'header': '',
            'page_access': 'no_access',
            'post_handler': (self.handlers['pages'], 'no_access')
        }
        self['missing_page'] = {
            'url': '',
            'template': 'missing',
            'title': 'Page Not Found',
            'page_access': 'no_access'
        }

        ## Sub Pages ##
        # Setup #
        self['setup_page']['sub_pages']['network_subpage'] = {
            'url': 'rf_network',
            'title': 'RF Network',
            'post_handler': (self.handlers['networks'], 'write')
        }
        self['setup_page']['sub_pages']['nodes_subpage'] = {
            'url': 'field_units',
            'title': 'Field Units',
            'post_handler': (self.handlers['platforms'], 'write')
        }
        self['setup_page']['sub_pages']['system_subpage'] = {
            'url': 'system',
            'title': 'System',
            'sub_pages': OrderedDict()
        }

        # System Sub Pages #
        self['setup_page']['sub_pages']['system_subpage']['sub_pages']['system_home'] = {
            'url': 'system_home',
            'title': 'System',
            'post_handler': (self.handlers['pages'], 'admin')
        }
        self['setup_page']['sub_pages']['system_subpage']['sub_pages']['alerts_acks'] = {
            'url': 'alerts_acks',
            'title': 'Alerts and Acks Settings',
            'post_handler': (self.handlers['alerts_acks'], 'write')
        }
        self['setup_page']['sub_pages']['system_subpage']['sub_pages']['snmp_agents'] = {
            'url': 'snmp_agents',
            'title': 'SNMP Agents',
            'post_handler': (self.handlers['snmp_agents'], 'write')
        }
        self['setup_page']['sub_pages']['system_subpage']['sub_pages']['snmp_commands'] = {
            'url': 'snmp_commands',
            'title': 'SNMP Commands',
            'post_handler': (self.handlers['snmp_commands'], 'write')
        }
        self['setup_page']['sub_pages']['system_subpage']['sub_pages']['snmp_traps'] = {
            'url': 'snmp_traps',
            'title': 'SNMP Traps',
            'traps_ws_enable': True,
            'post_handler': (self.handlers['snmp_traps'], 'write')
        }

        ## User Panel Pages ##
        self._user_panel_pages = OrderedDict()
        self._user_panel_pages['admin_page'] = {
            'url': 'admin',
            'title': 'Admin',
            'header': 'Admin Panel',
            'page_access': 'admin',
            'get_handler': (None, 'admin'),
            'post_handler': (self.handlers['users'], 'admin')
        }
        self._user_panel_pages['user_page'] = {
            'url': 'user',
            'title': 'User',
            'header': 'User Panel',
            'page_access': 'user',
            'get_handler': (None, 'user'),
            'post_handler': (self.handlers['users'], 'user')
        }

        ## Initialize Pages ##
        self.index_page = self.keys()[0]

        if not self.manager.system_settings.faq_enable:
            del self['faq_page']

        init_pages(self)
        init_pages(self._user_panel_pages)

    ## Public Methods ##
    def select_page(self, url):
        """ Selects page via page url """
        # LOGGER.debug("url 1 = " + str(url))
        self.__select_page(url.split('/'))
        # LOGGER.debug("url 2 = " + str(self.url()))

    def url(self, page=None):
        """ Returns selected page url """
        return self._parse('url', page)

    def template(self, page=None):
        """ Returns location of the template for the selected page """
        return self._parse('template', page)

    def template_html(self, page, template_name, **kwargs):
        """ Returns template html for the selected page """
        return template(os.path.join(self.template(page), template_name), **kwargs)

    def header(self):
        """ Returns selected page header """
        output = ''

        page_header = self._parse('header')
        if self.users.check_access('user') and not self['login_page']['selected']:
            output += "<h3><span id='page_header'>"
            output += page_header
            output += "</span><span id='page_header_extra'></span></h3>"
        else:
            output = '<h3>' + page_header + '</h3>'

        return output

    def title(self):
        """ Returns title of the selected page """
        page_title = self._parse('title')
        output = '<title>' + self.manager.system_settings.title() + ' - ' + page_title + '</title>'
        return output

    def html(self):
        """ Returns html of the selected page """
        output = ''

        page_access = self.users.check_access(self._parse('page_access'))
        if page_access:
            # special page or normal page
            page_template = self._parse('template')
            # LOGGER.debug("page tpl = " + page_template)
            output += template(page_template)

            overlay_enable = self.users.check_access('user')
            if overlay_enable:
                output += template('overlay')
        else:
            output += '<p>' + ACCESS_DENIED + '</p>'

        return output

    def buttons(self):
        """ Returns buttons for the selected page """
        return self.__buttons()

    # Cookie Related Methods #
    # Note: Have to have separate get and set cookie methods in order to set cookie to None!
    def default_cookie(self, page_name=None):
        """ Returns default cookie """
        return self._parse('cookies', page_name)

    def get_cookie(self, page_name=None):
        """ Fetches/Sets data for current page and cookie """
        cookie = None

        if (not self['login_page']['selected'] and not self['missing_page']['selected']) or page_name is not None:
            _url = self.url(page_name)

            if not (_url in self.users.current_user()['cookies']):
                cookie = self.default_cookie(page_name)
                self.users.update_current_user_cookies({_url: cookie})
            else:
                cookie = self.users.current_user()['cookies'][_url]
                if self.url('nodes_subpage') in _url:
                    new_cookie = self.platforms.flush_nodes(cookie)
                    if new_cookie != cookie:
                        cookie = self.set_cookie(new_cookie)

            # LOGGER.debug('url: {}'.format(_url))
            # LOGGER.debug('cookie: {}'.format(cookie))

        return cookie

    def set_cookie(self, value, page_name=None):
        """ Fetches/Sets data for current page and cookie """
        cookie = None

        if (not self['login_page']['selected'] and not self['missing_page']['selected']) \
                or page_name is not None:
            _url = self.url(page_name)
            if self.url('nodes_subpage') in _url:
                self._data_page_refresh()
            self.users.update_current_user_cookies({_url: value})
            cookie = value

        return cookie

    def reset_cookies(self):
        """ Resets cookies for a particular user """
        live_cookies = self.platforms.default_cookie('live')
        log_cookies = self.platforms.default_cookie('log')

        self.set_cookie(live_cookies, 'live_data')
        self.set_cookie(log_cookies, 'logs_data')
        self.set_cookie({}, 'nodes_subpage')

    # Group Methods #
    def get_group(self):
        """ Selects targeted group of nodes via provided url and template """
        group_url = None
        _url = self.url()
        _template = self.template()

        for data_page in ('live_data', 'logs_data'):
            if _url != self.url(data_page) and _template == self.template(data_page):
                group_url = _url.split('/')[-1]

        group = self.platforms.fetch_group_from_url(group_url)

        return group

    ## Private Methods ##
    def _parse(self, field, target_page_name=None, pages=None):
        """ Inner parser """
        output = None

        if pages is None:
            pages = self

        for page in pages.values():
            if target_page_name is None:
                if page['selected']:
                    if field in page:
                        output = page[field]

                    if 'sub_pages' in page:
                        suffix = self._parse(field, target_page_name, page['sub_pages'])
                        if suffix is not None:
                            if type(suffix) in (str, unicode) and field not in ('cookies', 'page_access', 'header'):
                                output += _midfix(field) + suffix
                            else:
                                output = suffix
                    break
            elif field in page:
                # LOGGER.debug("page = " + str(page))
                # LOGGER.debug("target_page = " + str(target_page))
                if target_page_name in pages.keys() \
                        and field in pages[target_page_name] \
                        and page[field] == pages[target_page_name][field]:
                    output = page[field]
                    break

                elif 'sub_pages' in page:
                    suffix = self._parse(field, target_page_name, page['sub_pages'])
                    if suffix is not None:
                        if type(suffix) in (str, unicode) and field not in ('cookies', 'page_access', 'header'):
                            output = page[field] + _midfix(field) + suffix
                        else:
                            output = suffix
                        break

        return output

    def _data_page_refresh(self):
        """ Updates number of pages for live and logs data """
        sub_pages_list = self.platforms.compose_group_urls()
        for page_name in ('live_data', 'logs_data'):
            data_page = self[page_name]

            # Create sub pages
            if len(sub_pages_list) > 1:
                # Initial page creation (if needed)
                if not ('sub_pages' in data_page):
                    data_page['sub_pages'] = OrderedDict()

                # Clear all the pages
                data_page['sub_pages'].clear()

                # Recreate pages
                for sub_page in sub_pages_list:
                    new_page = {
                        'url': sub_page['url'],
                        'title': sub_page['title'],
                        'header': ''
                    }
                    init_page(new_page)

                    del new_page['template']

                    data_page['sub_pages'][new_page['url']] = new_page

            # Remove sub pages
            elif 'sub_pages' in data_page:
                del data_page['sub_pages']

        return sub_pages_list

    ## Class-Private Methods ##
    def __select_page(self, url=None, pages=None, recursion_depth=0):
        """ Recursive inner select function """
        if url is None:
            url = list()

        if pages is None:
            pages = self

        for page in pages.values():
            page['selected'] = False

        if recursion_depth >= len(url):
            url.append('')

        display_login_page = not self.users.check_access('user')
        display_login_page |= self.users.current_user()['name'] == GUEST_USER['name']

        if self.users.check_access('user'):
            if url[recursion_depth]:
                for page_name, page in pages.items():
                    if (page_name != 'login_page' or display_login_page) and page_name != 'missing_page':
                        if page['url'] == url[recursion_depth]:
                            page['selected'] = True
                            # LOGGER.debug('Page Selected: ' + page_name)
                            if 'sub_pages' in page:
                                self.__select_page(url, page['sub_pages'], recursion_depth + 1)
                            break
                else:
                    if url[recursion_depth] in ('login', 'logout'):
                        # Select index page
                        pages.values()[0]['selected'] = True
                    else:
                        self['missing_page']['selected'] = True
            else:
                # Select index page
                pages.values()[0]['selected'] = True
        else:
            self['login_page']['selected'] = True

    def __buttons(self, prefix='', pages=None, recursion_depth=0):
        """ Internal button parser (Recursive function) """
        output = ''

        if pages is None:
            pages = self

        if not prefix:
            output += "\n<ul id='nav'>"
        else:
            output += '\n<ul>'

        display_login_page = not self.users.check_access('user') or \
                             self.users.current_user()['name'] == GUEST_USER['name']

        for page_name, page in pages.items():
            if (page_name != 'login_page' or (display_login_page and not self.manager.system_settings['user_bypass'])) \
                    and page_name != 'missing_page':
                # LOGGER.debug("page = " + str(page))
                if page['selected'] and not prefix:
                    output += "\n<li class='current'>"
                else:
                    output += "\n<li>"

                _url = page['url']
                if prefix:
                    _url = str(prefix) + '/' + _url

                if page_name == 'nodes_subpage':
                    output += "<a href='#' onclick='GoBase()'>"
                else:
                    output += '<a href="/' + _url + '">'

                output += page['title'] + '</a>'

                if page_name == 'nodes_subpage':
                    output += "\n<script><!--\n"

                    output += "$(document.body).append("
                    output += "\"<form id='" + page_name + "' action='/" + _url + "' method='post'>"
                    output += "<input type='hidden' name='action_method' value='load_base_page'>"
                    output += "</form>\");\n"

                    output += "function GoBase(){\n"
                    output += "$('#" + page_name + "').submit();\n"
                    output += "}\n"

                    output += "//--></script>\n"

                if 'sub_pages' in page and not self['login_page']['selected'] and recursion_depth < NAV_DEPTH:
                    output += self.__buttons(_url, page['sub_pages'], recursion_depth + 1)

        if not self.manager.system_settings['user_bypass']:
            if not display_login_page and not prefix:
                output += '\n<li><a href="/logout">' + LOG_OUT + '</a></li>'

        output += '\n</ul>'

        return output

    # User Panel Methods (Used by Users) #
    def __update_user_panel(self):
        """
        Update user panel depending on current user.
        E.g.: If current user admin - add admin page,
        if current user is not an admin - add user page

        :return: NA
        """
        # Remove user page
        for page_name in self._user_panel_pages.keys():
            if page_name in self.keys():
                del self[page_name]
                break

        # Add user page (if needed)
        if self.users.current_user()['name'] != GUEST_USER['name']:
            if self.users.check_access('admin'):
                page_name = 'admin_page'
            else:
                page_name = 'user_page'
            self.insert_after('diagnostics_page', (page_name, self._user_panel_pages[page_name]))

    def __select_user_panel(self):
        """
        Select user panel page depending on current user (Either admin or user page)

        :return: NA
        """
        # Select admin/user panel
        _url = None

        for page_name in self._user_panel_pages.keys():
            if page_name in self.keys():
                _url = self.url(page_name)
                break

        if _url:
            self.select_page(_url)
