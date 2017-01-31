
%### INCLUDES ###
%from py_knife import platforms

%from gate.main import system_settings, pages, users
%from gate.strings import IP_SCHEMES
%from gate.conversions import get_ip_scheme, get_net_addresses
%from gate.tpl import checked, OFF_ON, BYTE_ORDER, REGISTER_ORDER


%### CONSTANTS ###
%SYSTEM_INDEX = 0
%INDEX = None
%COOKIE = pages.get_cookie()
%if 'index' in COOKIE:
    %INDEX = COOKIE['index']
%end


%### HTML ###
<table class='hor-minimalist-b'>
    %## Static Header Names ##
    <thead><tr>
        %# Select Field for id
        %if users.check_access('admin'):
            <th scope='col'>Select</th>
        %end
        %#<th scope='col'>Name</th>
        <th scope='col'>Title</th>
        
        %ip_scheme = get_ip_scheme()
        
        %if ip_scheme == 'static' or platforms.PLATFORM not in platforms.EMBEDDED_PLATFORMS:
            <th scope='col'>IP Address</th>
            <th scope='col'>Subnet Mask</th>            
        %else:
            <th scope='col'>IP Addressing</th>
        %end

        %if system_settings.modbus_enable:
            <th scope='col'>Modbus Byte Order</th>
            <th scope='col'>Modbus Register Order</th>
        %end
        
        <th scope='col'>System Time</th>
        %#<th scope='col'>Timezone</th>
        <th scope='col'>Log Limit</th>
        <th scope='col'>Software</th>

    </tr></thead>
    
    %## Table Data ##
    <tr>
        %if users.check_access('admin'):
            <td><input type='radio' name='index' value="{{SYSTEM_INDEX}}" onchange="GetForm('form', {{SYSTEM_INDEX}})"
            {{checked(INDEX == SYSTEM_INDEX)}} ></td>
        %end
        %#<td>{{system_settings.name}}</td>
        <td>{{system_settings.title()}}</td>
        
        %if ip_scheme == 'static' or platforms.PLATFORM not in platforms.EMBEDDED_PLATFORMS:
            %ip_address, subnet_mask = get_net_addresses()
            <td>{{ip_address}}</td>
            <td>{{subnet_mask}}</td>            
        %else:
            <td>{{IP_SCHEMES[ip_scheme]}}</td>
        %end

        %if system_settings.modbus_enable:
            <td>{{BYTE_ORDER[int(system_settings['modbus_byte_order'])]}}</td>
            <td>{{REGISTER_ORDER[int(system_settings['modbus_register_order'])]}}</td>
        %end
        
        <td>{{system_settings.local_time()}}</td>
        %#<td>{{int(system_settings['timezone'])}}</td>
        <td>{{system_settings['log_limit']}}</td>
        <td>{{system_settings.version}}</td>
    </tr>
</table>
