"""
SNMP Agents related intricacies
"""

### INCLUDES ###
import os
import copy
import logging

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902

from py_knife.ordered_dict import OrderedDict
from py_knife.pickle import pickle_file

from gate.conversions import internal_name, get_net_addresses
from gate.database import DatabaseEntry, DatabaseDict, ModifiedOrderedDict

from ..common import SNMP_RESPONSES_PATH


### CONSTANTS ###
## Strings ##
SNMP_AGENT = '*SNMP Agent'

## SNMP Constants ##
SNMP_TIMEOUT = 1.0                  # seconds, has to be multiple of 0.5 due to low timer resolution
SNMP_RETRIES = 3
SNMP_AGENT_PORT = 161
SNMP_COMMUNITY = ['public', 'private']
SNMP_VERSIONS = ['SNMP v1', 'SNMP v2c']
SNMP_COMMAND_TYPES = {'get': 'Get', 'set': 'Set'}
SNMP_VALUE_TYPES = {
    'None': None,
    'integer': rfc1902.Integer,
    'string': rfc1902.OctetString,
    'OID': rfc1902.ObjectName,
    'IP address': rfc1902.IpAddress,
    'time ticks': rfc1902.TimeTicks
}

## Defaults ##
# SNMP Agents #
NEW_AGENT_DEFAULTS = {
    'name': '',
    'ip_address': '',
    'port': SNMP_AGENT_PORT,
    'snmp_community': SNMP_COMMUNITY[0],
    'snmp_version': SNMP_VERSIONS.index('SNMP v1')
}

TEST_AGENT = {
    'name': 'Test Agent',
    'ip_address': '192.168.0.123',
    'port': SNMP_AGENT_PORT,
    'snmp_community': SNMP_COMMUNITY[0],
    'snmp_version': SNMP_VERSIONS.index('SNMP v1')
}

DEFAULT_AGENTS = OrderedDict()
DEFAULT_AGENTS[internal_name(TEST_AGENT['name'])] = copy.deepcopy(TEST_AGENT)

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
def print_snmp_results(error_indication, error_status, error_index, var_binds):
    """ Check for errors and print out results. Use only for debugging! """
    if error_indication:
        print(error_indication)
    else:
        if error_status:
            LOGGER.debug('{0} at {1}'.format(
                str(error_status.prettyPrint()),
                str(error_index and var_binds[int(error_index) - 1] or '?')
            ))
        else:
            for oid, val in var_binds:
                LOGGER.debug('{0} = {1}'.format(
                    str(oid.prettyPrint()),
                    str(val.prettyPrint()))
                )


def _snmp_results(error_indication, error_status, error_index, var_binds):
    """ Return result of the SNMP get or set command """
    output = None
    if not error_indication:
        if not error_status:
            # Should be single value here!
            del var_binds[:-1]

            for oid, val in var_binds:
                output = val.prettyPrint()

    return output


def get_default_ip():
    """ Constructs default IP address """
    default_ip = '192.168.0.0'
    host_ip, host_mask = get_net_addresses()
    if host_ip is not None:
        default_ip = host_ip.split('.')
        default_ip[-1] = '0'
        default_ip = '.'.join(default_ip)
    return default_ip


### CLASSES ###
class SNMPAgent(DatabaseDict):
    # def __init__(self, name, ip_address, port, snmp_community, snmp_version):
    def __init__(self, **kwargs):
        # Key 'internal_name' is required for ModifiedOrderedDict!!!
        kwargs['internal_name'] = internal_name(kwargs['name'])
        super(SNMPAgent, self).__init__(
            defaults=kwargs
        )

        self.command_generator = cmdgen.CommandGenerator()

    def _address(self):
        """ Returns address of the Agent """
        address = (self['ip_address'], self['port'])
        return address

    def execute(self, snmp_command):
        """
        Execute Command
        Important: Please do not use directly!
        Add to the SNMP process queue instead!
        """
        snmp_address = snmp_command['oid']
        response = None

        if snmp_command['type'] in ('get', 'set'):
            try:
                if snmp_command['type'] == 'get':
                    response = self._get(snmp_address)

                elif snmp_command['type'] == 'set':
                    if 'value_type' in snmp_command and 'value' in snmp_command:
                        snmp_value = SNMP_VALUE_TYPES[snmp_command['value_type']](snmp_command['value'])
                        response = self._set(snmp_address, snmp_value)
                    else:
                        LOGGER.error("Command missing either value type or value! ")
            except:
                response = None

        else:
            LOGGER.error("No such SNMP command type!")

        pickle_file(SNMP_RESPONSES_PATH, response)

        return response

    def _get(self, snmp_address):
        """ Get AKA Read Command (Single commands ONLY!) """
        snmp_results = self.command_generator.getCmd(
            cmdgen.CommunityData(self['snmp_community'], mpModel=self['snmp_version']),
            cmdgen.UdpTransportTarget(self._address(), timeout=SNMP_TIMEOUT, retries=SNMP_RETRIES),
            snmp_address
        )

        # Use for debugging only!
        # print_snmp_results(*snmp_results)

        return _snmp_results(*snmp_results)

    def _set(self, snmp_address, snmp_value):
        """ Set AKA Write Command (Single commands ONLY!) """
        snmp_results = self.command_generator.setCmd(
            cmdgen.CommunityData(self['snmp_community'], mpModel=self['snmp_version']),
            cmdgen.UdpTransportTarget(self._address(), timeout=SNMP_TIMEOUT, retries=SNMP_RETRIES),
            (snmp_address, snmp_value)
        )

        # Use for debugging only!
        # print_snmp_results(*snmp_results)

        return _snmp_results(*snmp_results)


class SNMPAgents(ModifiedOrderedDict):
    def __init__(self):
        new_agent_defaults = NEW_AGENT_DEFAULTS
        new_agent_defaults['ip_address'] = get_default_ip()

        super(SNMPAgents, self).__init__(
            'internal_name',
            db_file=os.path.join('snmp', 'agents.db'),
            defaults=DEFAULT_AGENTS
        )

        # Name validation and default SNMP Agent value
        self.validation_string = SNMP_AGENT
        self._default_value = new_agent_defaults

    def _load_default(self):
        """ Loads main with defaults """
        return DatabaseEntry._load_default(self)

    def load(self):
        """ Overwriting default load method (dictionaries -> instances) """
        super(SNMPAgents, self).load()

        if len(self._main):
            self.main.clear()
            for snmp_agent_name, snmp_agent_kwargs in self._main.items():
                self.main[snmp_agent_name] = SNMPAgent(**snmp_agent_kwargs)

    def save(self, db_content=None):
        """ Overwriting default save method (instances -> dictionaries) """
        for snmp_agent_name, snmp_agent in self.main.items():
            self._main[snmp_agent_name] = dict(snmp_agent.items())

        super(SNMPAgents, self).save()
