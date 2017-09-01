"""
String Related Constants
"""

### INCLUDES ###
# from datetime import date

### CONSTANTS ###
## Mesh Network Strings ##
FIELD_UNIT = 'Field unit'
UNKNOWN_ERROR = "Unknown Error Occurred!"

## Web Template Strings ##
VALIDATION_FAIL = "One of the fields was entered incorrectly!"
NO_NODE = "No such field unit in the database!"
NO_NODES = "No field units have been detected!"
NO_ACTIVE_NODES = "No active field units are present!"
NO_ACTIVE_PLATFORMS = "No active platforms!"                # Never will be used most likely
NO_VIRGINS = "No virgins are presents!"
ADC_DEFAULT_VALUES = "Sensor parameters are filled with default values!"
DATA_MISMATCH = "Data Mismatch error occurred. Your browser will refresh" + \
    " current page automatically after error is resolved!"
NO_USERS = "Database does not have any users!"
REBOOT = "Reboot!"
LOG_EMPTY = "This log is empty!"
LOG_ALREADY_EMPTY = "This log is already empty!"

## SNMP Test Strings ##
TEST_SUCCESS1 = "Success! SNMP Agent response: "
TEST_SUCCESS2 = "!"
TEST_FAILURE = "SNMP Agent failed to respond to the request!"

## Main page template ##
NO_JAVASCRIPT = "Sorry, your browser does not support JavaScript!"
#FOOTER = str(date.today().year) + " All Rights Reserved"
SUCCESS = "Success!"
WEBSOCKET_ERROR = "Your browser does not support WebSockets!" + \
    " Please upgrade your browser to the latest version."
ONLINE = "Online"
AWAKE = "Awake!"
SLEEP = "Sleep!"
OFFLINE = "Offline"

## Software File Messages ##
NO_FILE = "File have not been selected!"
WRONG_FILENAME = "Wrong File Name!"
WRONG_EXTENSION = "Wrong File Extension!"
WRONG_FILE_FORMAT = "Wrong File Format!"

## Software Upload Titles ##
SOFTWARE_UPDATE = 'Software Update'
UPDATE_HEADERS = {
    'network_update': 'Network Update',
    'inactive_update': 'Network Update on Inactive Field Unit',
    'preset_update': 'Network Settings Preset',
    'node_update': 'Field Unit Update',
    'log_export': 'Log Export Menu',
    'database_export': 'Database Export Menu',
    'database_import': 'Database Import Menu'
}

# Log/Database Export Progress #
PROCESSING = 'Processing:'
FAILED = ' Failed!'
COMPLETE = ' is Complete!'
CANCELLED = ' has been cancelled!'
REBOOT_REQUIRED = "System will go offline now while performing reboot!" \
                  " Please refresh your web browser in couple minutes!"
RESTART_REQUIRED = "System will be shut down! Please restart gate application!"
BASE_REBOOT_COMPLETED = "Bridge reboot is completed!"

## Software Upload Messages ##
UPLOAD_PROGRESS = "Progress: "
UPLOAD_NODE1 = "Updating node '"
UPLOAD_NODE2 = "' ("
UPLOAD_NODE3 = " of "
UPLOAD_NODE4 = "): "
UPLOAD_BASE = "Updating Base node: "

UPLOAD_WARNING = "Software update will halt the whole system temporarily!"
UNPACK_ERROR = 'Database Import failed due to unpacking error!'
SOME_TIME = " Might take couple minutes..."
UPLOAD_SAVING = "Saving provided archive." + SOME_TIME
UPLOAD_UNPACKING = "Unpacking uploaded archive." + SOME_TIME
IMPORT_IN_PROGRESS = "Importing New Database!" + SOME_TIME

USER_WARNING = "Warning: You about to modify current user!" + \
    " All changes will take immediate effect!"

## IP Schemes ##
IP_SCHEMES = {'dynamic': 'Dynamic', 'static': 'Static'}

## Network Update Messages ##
NODE_UPDATE = 'Field Unit update'
NETWORK_UPDATE = 'Network update'
PRESET_UPDATE = 'Network preset'
INACTIVE_NODE_UPDATE = " on inactive node "
BASE_NODE_UPDATE = " on base node "
NODE_NODE_UPDATE = " on node "
REQUEST_UPDATE = " has been requested!"
SUCCESS_UPDATE = " executed successfully!"
REQUEST_CANCEL_UPDATE = " is being cancelled!"
SUCCESS_CANCEL_UPDATE = " cancelled successfully!"
IGNORED_UPDATE = " will be ignored!"
SYNC_WAITING = "Waiting for the next sync..."
NODES_WAITING = "Waiting for the rest of the field units to "
VERIFY_WAITING = NODES_WAITING + "verify changes..."
CANCEL_WAITING = NODES_WAITING + "roll back changes..."
MANUAL_SYNC = "Manual Sync: "
UPDATING1 = "Updating "
UPDATING2 = " to '"
UPDATING_NETWORK = "' on network "
UPDATING_NODE = "' on node "
UPDATE_COMPLETE = ' is successfully completed!'
UPDATE_CANCELLED = ' has been cancelled!'
