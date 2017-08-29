"""
System Settings Web Handler with integrated Edit Methods
"""

### INCLUDES ###
import os
import time
import zipfile
import glob
import logging

from bottle import request, static_file
# from tornado import ioloop, gen
from Crypto import Random

from py_knife import aes, file_system, upload, zip, ordered_dict

from gate import common, strings
from gate.update_interface import WorkerThread
from gate.sleepy_mesh import SYSTEM_STATISTICS_FILE
from gate.sleepy_mesh.node.common import NETWORK_UPDATE_FIELDS

from gate.web.pages.handlers import WebHandlerBase


### CONSTANTS ###
## Some Delays ##
SAFETY_DELAY = 0.5              # seconds

## Strings ##
ARCHIVING_DATABASE = 'Archiving database...'

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### CLASSES ###
class WebHandler(WebHandlerBase):
    def __init__(self, pages):
        super(WebHandler, self).__init__(pages, pages.manager.system_settings)
        self._database_import = None
        self._database_export = None

    def _update_system(self, cookie):
        """ Updates general settings of an indexed system """
        validate = True

        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        # Get data from forms
        title = request.forms.title.encode('ascii', 'ignore')
        log_limit = int(request.forms.log_limit)
        warnings_pop_up_enable = bool(request.forms.warnings_pop_up_enable)
        warnings_sound_enable = bool(request.forms.warnings_sound_enable)

        # Make sure title is not empty and not too long
        validate &= title and (len(title) <= common.TITLE_MAX_LENGTH)
        # Make sure log limit is valid
        validate &= (50 <= log_limit <= 1000)

        ip_scheme = request.forms.ip_scheme
        ip_address = request.forms.ip_address
        subnet_mask = request.forms.subnet_mask
        if ip_scheme and ip_address and subnet_mask:
            ip_scheme = ip_scheme.encode('ascii', 'ignore')
            ip_address = ip_address.encode('ascii', 'ignore')
            subnet_mask = subnet_mask.encode('ascii', 'ignore')

            # Validate data
            validate_list = [ip_address, subnet_mask]
            for address in validate_list:
                for value in address.split('.'):
                    validate &= (0 <= int(value) <= 255)

        if validate:
            # Create save dictionary
            save_dict = {
                'title': title,
                'log_limit': log_limit,
                'warnings_pop_up_enable': warnings_pop_up_enable,
                'warnings_sound_enable': warnings_sound_enable
            }

            if request.forms.time and request.forms.timezone:
                # Get data from forms
                web_time = float(request.forms.time)
                timezone = float(request.forms.timezone)

                # Change time
                time_offset = time.time() - web_time
                time_diff = self._object['time_offset'] - time_offset
                self._object['time_offset'] = time_offset
                self._object['timezone'] = timezone

                if time_diff:
                    # Change time
                    self._manager.update_timing(time_diff)
                    # Confirm change
                    self._manager.websocket.send(self._object.time_settings_str())

            if ip_scheme and ip_address and subnet_mask:
                if self._object.change_network_settings(ip_scheme, ip_address, subnet_mask):
                    self._manager.snmp_server.restart()

            self._object.update(save_dict)
            self._object.save()
        else:
            return_dict['kwargs']['alert'] = strings.VALIDATION_FAIL

        return return_dict

    def _update_modbus(self, cookie):
        """ Updates modbus settings of an indexed system """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if self._manager.system_settings.modbus_enable:
            # Enable/Disable Modbus #
            modbus_enable = request.forms.modbus_enable
            if modbus_enable:
                modbus_enable = int(modbus_enable)
                if modbus_enable != self._manager.system_settings.modbus_enable:
                    self._manager.system_settings.modbus_enable = modbus_enable
                    if modbus_enable:
                        self._manager.modbus_server.start()
                    else:
                        self._manager.modbus_server.stop()

            # Modbus byte order and register format #
            modbus_byte_order = bool(int(request.forms.modbus_byte_order))
            modbus_register_order = bool(int(request.forms.modbus_register_order))

            # Create save dictionary
            save_dict = {
                'modbus_byte_order': modbus_byte_order,
                'modbus_register_order': modbus_register_order
            }

            self._object.update(save_dict)
            self._object.save()

            # Modbus Units #
            active_platforms = self._manager.platforms.active_platforms()
            for platform_name, platform in active_platforms.items():
                display_headers = platform.read_headers('display').values()
                for header in display_headers:
                    header_name = header['internal_name']
                    new_units = request.forms.get(platform_name + '_' + header_name + '_units')
                    header.modbus_units(new_units)

        return return_dict

    def _start_database_import(self, cookie):
        """ Save database settings to E10 """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        # Make sure user made file selection
        database_file = request.files.data
        if not database_file:
            return_dict['kwargs']['alert'] = strings.NO_FILE

        # Get data from form
        else:
            # Split filename
            filename, extension = os.path.splitext(database_file.filename.lower())

            if extension != '.dea':
                return_dict['kwargs']['alert'] = strings.WRONG_EXTENSION

            else:
                if self._database_import is not None:
                    self._database_import.stop()

                self._database_import = DatabaseImportThread(self._pages, database_file)
                self._database_import.start()

        return return_dict

    def _cancel_database_import(self, cookie):
        """ Cancels Database Import """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if self._database_import is not None:
            self._database_import.stop()
            self._database_import = None

        return return_dict

    def _start_database_export(self, cookie):
        """ Upload database settings from E10 """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if self._database_export is not None:
            self._database_export.stop()

        self._database_export = DatabaseExportThread(self._pages)
        self._database_export.start()

        return return_dict

    def _finish_database_export(self, cookie):
        """ Finishes Database Export by providing zip file """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        database_name = file_system.fetch_file(os.path.join(common.UPLOADS_FOLDER, '*.dea'))

        if database_name:
            if os.path.getsize(os.path.join(common.UPLOADS_FOLDER, database_name)) > 0:
                return_dict['new_page'] = static_file(
                    database_name, root=common.UPLOADS_FOLDER, download=True)
                # LOGGER.debug("MimeType: " + str(return_dict['new_page']['Content-Type']))

        else:
            return_dict['kwargs']['alert'] = strings.UNKNOWN_ERROR

        if self._database_export is not None:
            self._database_export.stop()
        self._database_export = None

        return return_dict

    def _cancel_database_export(self, cookie):
        """ Cancels Database Export """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        if self._database_export is not None:
            self._database_export.stop()
            self._database_export = None

        return return_dict

    def _remove_database(self, cookie):
        """ Removes Database """
        return_dict = {
            'kwargs': {},
            'save_cookie': False
        }

        self._manager.reset_network(force_reset=True, complete_callback=self.__silence_scheduler_callback)

        return return_dict

    def __silence_scheduler_callback(self):
        """ Silence Scheduler callback """
        self._manager.silence_scheduler(complete_callback=self.__remove_database_callback)

    def __remove_database_callback(self):
        """ Remove database callback """
        # Delete Nodes
        nodes = self._manager.platforms.select_nodes('all').values()
        for node in nodes:
            self._manager.platforms.delete_node(node)

        # Remove files
        file_system.remove_files(os.path.join(common.DATABASE_FOLDER, '*'))

        # Reload databases
        self._manager.reload_databases()

        # Reset cookies
        self._pages.reset_cookies()

        # Resume Scheduler
        self._manager.resume_scheduler()


class DatabaseImportThread(WorkerThread):
    def __init__(self, pages, data):
        super(DatabaseImportThread, self).__init__()
        self._pages = pages
        self._manager = self._pages.manager
        self._data = data
        self._update_interface = self._manager.update_interfaces.create(('database_import', ))
        self._finish_message = None

    def run(self):
        """ Performs database import """
        self.set_running(True)
        self._update_interface.start_update('database_import')
        self._manager.websocket.send(strings.UPLOAD_SAVING, 'ws_init', 0.0)

        # Yield so web page fetched first before processing this request
        time.sleep(SAFETY_DELAY)
        # FIXME: Bellow method is for the schedule() method and not for the separate thread
        # yield gen.Task(ioloop.IOLoop.instance().add_timeout, time.time() + SAFETY_DELAY)

        if self.get_running():
            self._database_import()

        else:
            self.__finish_database_import()

    def _database_import(self):
        """ Database Import """
        execute_callback = True

        # Remove old files
        file_system.empty_dir(common.UPLOADS_FOLDER)
        file_path = upload.save_upload(common.UPLOADS_FOLDER, self._data)

        if not file_path:
            self._finish_message = strings.UNKNOWN_ERROR

        elif self.get_running():
            # Decrypting archive
            self._manager.websocket.send(strings.UPLOAD_UNPACKING, 'ws_init', 15.0)

            filename, extension = os.path.splitext(self._data.filename.lower())
            zip_path = os.path.join(common.UPLOADS_FOLDER, filename + '.zip')
            database_password = self._manager.system_settings.database_password
            if aes.decrypt(file_path, zip_path, database_password):
                if self.get_running():
                    # Extracting zip
                    self._manager.websocket.send(strings.UPLOAD_UNPACKING, 'ws_init', 25.0)
                    success = zip.extract_zip(zip_path)
                    if success:
                        if self.get_running():
                            self._manager.websocket.send(strings.IMPORT_IN_PROGRESS, 'ws_init', 50.0)

                            file_system.remove_file(zip_path)

                            # Silence Scheduler
                            self._manager.silence_scheduler(complete_callback=self.__database_import)

                            execute_callback = False

                    else:
                        self._finish_message = strings.UNPACK_ERROR

            else:
                self._finish_message = strings.WRONG_FILE_FORMAT

        if execute_callback:
            self.__finish_database_import()

    def __database_import(self):
        """ Database Import Internals """
        database_path = os.path.join(common.UPLOADS_FOLDER, 'database')

        # Save old network settings
        old_network = ordered_dict.OrderedDict()
        for network_field in NETWORK_UPDATE_FIELDS:
            old_network[network_field] = self._manager.networks[0][network_field]

        LOGGER.debug('old_network: ' + str(old_network))

        # Remove old db files
        db_files_paths = os.path.join(common.DATABASE_FOLDER, '*')
        db_exclude_paths = [os.path.join(common.DATABASE_FOLDER, SYSTEM_STATISTICS_FILE)]

        LOGGER.debug("DB content 1: " + str(glob.glob(db_files_paths)))
        file_system.remove_files(db_files_paths, db_exclude_paths)
        LOGGER.debug("DB content 2: " + str(glob.glob(db_files_paths)))

        # Copy files
        file_system.copy_dir(database_path, common.DATABASE_FOLDER)

        # Reload databases
        self._manager.reload_databases()

        # Save new network settings
        new_network = ordered_dict.OrderedDict()
        for network_field in NETWORK_UPDATE_FIELDS:
            new_network[network_field] = self._manager.networks[0][network_field]

        LOGGER.debug('new_network: ' + str(new_network))

        # Overwrite network settings to proper ones (old network settings)
        for network_field, network_value in old_network.items():
            self._manager.networks[0][network_field] = network_value

        # Reset cookies
        # self._pages.reset_cookies()
        self._pages.set_cookie({}, 'nodes_subpage')

        # Resume Scheduler
        self._manager.resume_scheduler()
        self._manager.websocket.send(strings.IMPORT_IN_PROGRESS, 'ws_init', 75.0)

        self._manager.request_update(
            new_network,
            complete_callback=self.__finish_database_import
        )

    def __finish_database_import(self):
        """ Import Complete Callback """
        status = self.get_running()
        if status is False:
            file_system.empty_dir(common.UPLOADS_FOLDER)

        if self._finish_message is None:
            _finish_message = 'Database Import'
            if status is False:
                self._finish_message = _finish_message + strings.FAILED
            else:
                self._finish_message = _finish_message + strings.COMPLETE

        self._update_interface.finish_update(self._finish_message)

        self.set_running(False)


class DatabaseExportThread(WorkerThread):
    def __init__(self, pages):
        super(DatabaseExportThread, self).__init__()
        self._pages = pages
        self._manager = self._pages.manager
        self._update_interface = self._manager.update_interfaces.create(('database_export', ))

    def run(self):
        """ Creates database file """
        self.set_running(True)

        self._update_interface.start_update('database_export')

        # Yield so web page fetched first before processing this request
        time.sleep(SAFETY_DELAY)
        # FIXME: Bellow method is for the schedule() method and not for the separate thread
        # yield gen.Task(ioloop.IOLoop.instance().add_timeout, time.time() + 0.5)

        zip_file = None
        if self.get_running():
            # Remove old files
            file_system.remove_files(os.path.join(common.UPLOADS_FOLDER, '*'))

        if self.get_running():
            # Silence Scheduler
            self._manager.silence_scheduler(complete_callback=self.__database_export)

        else:
            self.__finish_database_export(zip_file)

    def __database_export(self):
        """ Performs database export """
        zip_file = None
        if self.get_running():
            database_filename = 'database_' + self._manager.system_settings.create_time_stamp()
            zip_path = os.path.join(common.UPLOADS_FOLDER, database_filename)
            zip_file = self.__create_zip(zip_path, common.DATABASE_FOLDER)

            # Resume Scheduler
            self._manager.resume_scheduler()

        self.__finish_database_export(zip_file)

    def __create_zip(self, zip_path, files_path):
        """ Creates Zip Archive """
        zip_file = zip_path

        try:
            zip_archive = zipfile.ZipFile(zip_path + '.zip', 'w')

            current_file = 0.0
            total_files = 0.0
            for root, dirs, files in os.walk(files_path):
                total_files += len(files)

            files_path_len = len(files_path.split(os.sep))
            for root, dirs, files in os.walk(files_path):
                for _file in files:
                    if self.get_running():
                        current_file += 1.0
                        progress_message = strings.PROCESSING + 'file {0:>3} out of {1:>3} files!'.format(
                            int(current_file), int(total_files))
                        progress_percentage = ((current_file - 1.0) / total_files) * 80.0
                        self._manager.websocket.send(
                            progress_message, 'ws_init', progress_percentage)

                        _file_path = os.path.join(root, _file)
                        _file_path_list = _file_path.split(os.path.sep)[files_path_len - 1:]
                        _dest_path = os.path.join(*_file_path_list)

                        # LOGGER.debug('source: ' + str(_file_path))
                        # LOGGER.debug('destination: ' + str(_dest_path))

                        # Archive file
                        file_name = os.path.basename(_file_path)
                        # Do not include system statistics file
                        if file_name != SYSTEM_STATISTICS_FILE:
                            LOGGER.debug("Archiving : " + str(file_name))
                            zip_archive.write(_file_path, _dest_path)

                    else:
                        zip_file = None
                        break

            zip_archive.close()

            # Encrypting Archive
            self._manager.websocket.send(ARCHIVING_DATABASE, 'ws_init', 90.0)
            database_password = self._manager.system_settings.database_password
            if not aes.encrypt(zip_path + '.zip', zip_path + '.dea', database_password):
                # Otherwise, encrypt does not work correctly
                # FIXME: Not very elegant fix...
                Random.atfork()

                if not aes.encrypt(zip_path + '.zip', zip_path + '.dea', database_password):
                    zip_file = False

        except:
            zip_file = False

        return zip_file

    def __finish_database_export(self, zip_file):
        """ Finish export """
        message = 'Database Export'
        if zip_file is None:
            message += strings.CANCELLED
        elif zip_file is False:
            message += strings.FAILED
        else:
            message += strings.COMPLETE

        self._update_interface.finish_update(message)
        self.set_running(False)
