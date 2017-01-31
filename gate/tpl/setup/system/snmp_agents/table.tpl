
%### INCLUDES ###
%from gate.main import pages, snmp_agents
%from gate.snmp import SNMP_VERSIONS
%from gate.tpl import checked


%### CONSTANTS ###
%INDEX = None
%COOKIE = pages.get_cookie()
%if 'index' in COOKIE:
    %INDEX = COOKIE['index']
%end


%### HTML ###
%if not defined('table_only'):
    <p><span class="float_right">
        <input type="button" onclick="location.href='/{{pages.url('system_home')}}'" value="Back">
    </span></p>
%end

%if len(snmp_agents):
    <table class='hor-minimalist-b'>
        %# Static Header Names
        <thead><tr>
            %if not defined('table_only'):
                %# Select field for user id
                <th scope='col'>Select</th>
            %end
            <th scope='col'>Name</th>
            <th scope='col'>IP Address</th>
            <th scope='col'>Port</th>
            <th scope='col'>SNMP Community</th>
            <th scope='col'>SNMP Version</th>
        </tr></thead>
    
        %#Table Data
        %for snmp_agent_key, snmp_agent in snmp_agents.items():
            <tr>
                %if not defined('table_only'):
                    <td>
                        <input type='radio' name='index' value="{{snmp_agent_key}}"
                        onchange="GetForm('form', '{{snmp_agent_key}}')"
                        {{checked(INDEX == snmp_agent_key)}} >
                    </td>
                %end
                <td>{{snmp_agent['name']}}</td>
                <td>{{snmp_agent['ip_address']}}</td>
                <td>{{snmp_agent['port']}}</td>
                <td>{{snmp_agent['snmp_community']}}</td>
                <td>{{SNMP_VERSIONS[snmp_agent['snmp_version']]}}</td>
            </tr>
        %end
    </table>
%end

%if not defined('table_only'):
    %# New SNMP Agent Button
    <p><input type='button' value='Create New SNMP Agent' onclick="CreateNew()" /></p>
%end
