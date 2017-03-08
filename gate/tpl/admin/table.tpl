
%### INCLUDES ###
%from gate.main import system_settings, pages, users
%from gate.strings import NO_USERS
%from gate.tpl import checked


%### CONSTANTS ###
%USER_KEY = None
%COOKIE = pages.get_cookie()
%if 'index' in COOKIE:
    %USER_KEY = COOKIE['index']
%end

%## Enable/Disable Strings ##
%ENABLE_DISABLE_DICT = {True: 'Disable', False: 'Enable'}


%### HTML ###
%if not len(users):
    <p><small>Error: {{NO_USERS}}</small></p>
%else:
    %### ADMIN PANEL ###
    <table class='hor-minimalist-b'>
        %# Static Header Names
        <thead><tr>
            %# Select field for user id
            <th scope='col'>Select</th>
            <th scope='col'>Username</th>
            %#<th scope='col'>Password</th>
            <th scope='col'>Active</th>
            <th scope='col'>Read</th>
            <th scope='col'>Write</th>
            <th scope='col'>Admin</th>
        </tr></thead>
    
        %#Table Data
        %for user_key, user in users.items():
            <tr>
                <td>
                    <input type='radio' name='index' value="{{user_key}}"
                    onchange="GetForm('form', '{{user_key}}')"
                    {{checked(USER_KEY == user_key)}} >
                </td>
                <td>{{user['name']}}</td>
                %#<td>{{user['password']}}</td>
                <td>{{user['active']}}</td>
                <td>{{users.check_access('read', user)}}</td>
                <td>{{users.check_access('write', user)}}</td>
                <td>{{users.check_access('admin', user)}}</td>
            </tr>
        %end
    </table>
    
    %# New User Button
    <span class="float_left">
        <p><input type='button' value='Create New User' onclick="CreateNew()" /></p>
    </span>
    %# Create, Cancel Buttons
    <span class="float_right">
        <p><form action='/{{pages.url()}}' method='post'>
            <input type='hidden' name='action_method' value='toggle_user_bypass' >
            <input type='submit' name='admin_submit' value="{{ENABLE_DISABLE_DICT[system_settings['user_bypass']]}} User Bypass" >
        </form></p>
    </span>

%end
