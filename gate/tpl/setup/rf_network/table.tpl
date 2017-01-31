
%### INCLUDES ###
%from gate.main import manager, pages, users
%from gate.tpl import DATA_RATE, OFF_ON, checked


%### CONSTANTS ###
%INDEX = None
%COOKIE = pages.get_cookie()
%if 'index' in COOKIE:
    %INDEX = COOKIE['index']
%end


%### HTML ###
<table class='hor-minimalist-b'>
    %# Static Header Names
    <thead><tr>
        %# Select Field for id
        %if users.check_access('write'):
            <th scope='col'>Select</th>
        %end
        %#<th scope='col'>Network ID</th>
        <th scope='col'>Channel</th>
        <th scope='col'>Data Rate</th>
        %#<th scope='col'>Receive Group</th>
        %#<th scope='col'>Forward Group</th>
        %#<th scope='col'>AES Key</th>
        <th scope='col'>AES Enable</th>
        <th scope='col'>Wake Period, s</th>
        <th scope='col'>Sleep Period, s</th>
        <th scope='col'>Timeout Wake Period, s</th>
        <th scope='col'>Timeout Sleep Period, s</th>
        <th scope='col'>Firmware</th>
        <th scope='col'>Software</th>
    </tr></thead>

    %# Table Data
    %for index, network in enumerate(manager.networks):
        <tr>
            %if users.check_access('write'):
                <td><input type='radio' name='index' value="{{index}}"
                onchange="GetForm('form', {{index}})"
                {{checked(INDEX == index)}} ></td>
            %end
            %#<td>{{network['net_id']}}</td>
            <td>{{network['channel']}}</td>
            <td>{{DATA_RATE[network['data_rate']]}}</td>
            %#<td>{{network['rGroup']}}</td>
            %#<td>{{network['fGroup']}}</td>
            %#<td>{{network['aes_key']}}</td>
            <td>{{OFF_ON[network['aes_enable']]}}</td>
            <td>{{network['wake']}}</td>
            <td>{{network['sleep']}}</td>              
            <td>{{network['timeout_wake']}}</td>
            <td>{{network['timeout_sleep']}}</td>
            <td>{{network['firmware']}}</td>
            <td>{{network['software']}}</td>
        </tr>
    %end
</table>
