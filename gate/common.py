"""
Collection of global common constants and functions
Mostly ones that are shared by setup.py and gate module
"""

### INCLUDES ###
import os
import inspect

from optparse import OptionParser

from py_knife import platforms


### CONSTANTS ###
## Option Parser ##
OPTIONS_PARSER = OptionParser()
OPTIONS_PARSER.add_option('-s', '--system', dest='system_name', default='swe', help='Specify system name')
OPTIONS_PARSER.add_option('-l', '--language', dest='language', default='english', help='Specify system language')
OPTIONS_PARSER.add_option('-m', '--modbus', dest='modbus_enable', action='store_false', default=True,
                          help='Include this option to disable modbus')
OPTIONS_PARSER.add_option('-n', '--snmp', dest='snmp_enable', action='store_false', default=True,
                          help='Include this option to disable SNMP')
OPTIONS_PARSER.add_option('-f', '--faq', dest='faq_enable', action='store_true', default=False,
                          help='Enable frequently asked questions page')
OPTIONS_PARSER.add_option('-v', '--virgins', dest='virgins_enable', action='store_true', default=False,
                          help='Enable virgin detection and upload')
OPTIONS_PARSER.add_option('-b', '--button', dest='manual_log', action='store_true', default=False,
                          help='Enable manual logging button')

## OS Files/Folders ##
FILE_SYSTEM_ROOT = os.path.abspath(os.sep)
ETC_FOLDER = os.path.join(FILE_SYSTEM_ROOT, 'etc')
INITD_FOLDER = os.path.join(ETC_FOLDER, 'init.d')
IP_ADDR_FOLDER = os.path.join(FILE_SYSTEM_ROOT, 'home', 'ip_addr')
FTP_FILE = os.path.join(INITD_FOLDER, 'ftp')
AUTO_START_FILE = os.path.join(INITD_FOLDER, 'S999snap')

## User Data Folders ##
if platforms.PLATFORM == platforms.SYNAPSE_E10:
    CWD = os.path.join(FILE_SYSTEM_ROOT, 'root')
else:
    # This is not set properly at the startup on E10 for some reason
    CWD = os.path.expanduser('~')

GATE_FOLDER = os.path.join(CWD, 'gate_data')
DOCS_FOLDER = os.path.join(GATE_FOLDER, 'docs')
LOGS_FOLDER = os.path.join(GATE_FOLDER, 'logs')
UPLOADS_FOLDER = os.path.join(GATE_FOLDER, 'uploads')
DATABASE_FOLDER = os.path.join(GATE_FOLDER, 'database')
SYSTEM_FOLDER = os.path.join(GATE_FOLDER, 'system')

## Web(Media) Folders ##
MWD = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
IMG_FOLDER = os.path.join(MWD, 'img')
TPL_FOLDER = os.path.join(MWD, 'tpl')

## Process Niceness ##
SIDE_PROCESS_NICENESS = 5         # -20(highest priority) to 20(lowest priority), our main runs at 0

## Other Web Constants ##
TITLE_MAX_LENGTH = 25
LIVE_NODES_NUMBER = 10
