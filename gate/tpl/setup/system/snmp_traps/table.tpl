
%### INCLUDES ###
%from gate.main import pages, snmp_traps
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

%if len(snmp_traps):
    <table class='hor-minimalist-b'>
        %# Static Header Names
        <thead><tr>
            %if not defined('table_only'):
                %# Select field for user id
                <th scope='col'>Select</th>
            %end
            <th scope='col'>Name</th>
            <th scope='col'>OID</th>
            <th scope='col'>Value</th>
        </tr></thead>
    
        %#Table Data
        %for snmp_trap_key, snmp_trap in snmp_traps.items():
            <tr>
                %if not defined('table_only'):
                    <td>
                        <input type='radio' name='index' value="{{snmp_trap_key}}"
                        onchange="GetForm('form', '{{snmp_trap_key}}')"
                        {{checked(INDEX == snmp_trap_key)}} >
                    </td>
                %end
                <td>{{snmp_trap['name']}}</td>
                <td>{{snmp_trap['oid']}}</td>
                <td>{{snmp_trap['value']}}</td>
            </tr>
        %end
    </table>
%end

%if not defined('table_only'):
    %# New SNMP Agent Button
    <p><input type='button' value='Create New SNMP Trap' onclick="CreateNew()" /></p>
%end
