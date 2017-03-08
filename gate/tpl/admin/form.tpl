
%### INCLUDES ###
%import copy
%import json

%from gate.main import pages, users
%from gate.strings import USER_WARNING
%from gate.tpl import checked, disabled
%from gate.web.users import ACCESS, GUEST_USER


%### CONSTANTS ###
%URL = pages.url()
%USER_KEY = pages.get_cookie()['index']
%USER = users.get_user(USER_KEY)


%### JS ###
<script><!--

%# Initialize user_name_taken and admin_present variables
GetUserValidation();

function validate_admin_form(form)
{
    if (form.action_method.value == 'update_user')
    {
        if (form.username.value == "" || form.username.value == null) 
        {
            alert("Username can not be empty!");
            form.username.focus();
            return false;
        }
%if USER['name'] != GUEST_USER['name']:
    %if USER_KEY in users.keys():
        else if (form.password1.value == "" || form.password1.value == null)
        {
            alert("Password can not be empty!");
            form.password1.focus();
            return false;
        }
    %end
        else if (form.password1.value != form.password2.value)
        {
            alert("Password fields do not match! Try again!");
            form.password1.value = '';
            form.password2.value = '';
            form.password1.focus();
            return false;
        }
%end
        else if (user_name_taken == true)
        {
            alert("This username is taken already!");
            form.username.focus();
            return false;
        }
        else if (admin_present == false)
        {
            alert("System must have at least one admin!");
            return false;
        }
    }
    else if (form.action_method.value == 'remove')
    {        
        if(admin_present == false)
        {
            alert("System must have at least one admin!");
            return false;
        }
    }

    %# Test that JS works properly
    %# alert('Success!')
    return true;
}

function getKeyByValue(dictionary, value)
{
    for(var prop in dictionary)
    {
        if(dictionary.hasOwnProperty(prop))
        {
            if(dictionary[prop] === value)
                return prop;
        }
    }
}

function Permissions(access)
{
    var AccessLevels = JSON.parse('{{!json.dumps(ACCESS)}}');
    
    $("input[name='access']").each(function() {
        if (AccessLevels[access] > AccessLevels[$(this).val()])
            $(this).prop('checked', true);
        else if (AccessLevels[access] == AccessLevels[$(this).val()])
        {
            if (!$(this).prop('checked'))
                access = getKeyByValue(AccessLevels, AccessLevels[access] - 10)
        }
        else if (AccessLevels[access] < AccessLevels[$(this).val()])
            $(this).prop('checked', false);
    });
    
    %# console.log(access);
    $("input[name='total_access']").val(access);

    GetUserValidation();
}

//--></script>

%### HTML ###
<form action='/{{URL}}' onsubmit='return validate_admin_form(this)' method='post' ><fieldset>
    
    %if USER_KEY in users.keys():
        <legend><h3>User Update</h3></legend>
        %if users.current_user() == USER:
            <p class="current_user" ><small>{{USER_WARNING}}</small></p>
        %end
    %else:
        <legend><h3>New User</h3></legend>
    %end

    <input type='hidden' name='action_method' value='update_user' >
    <input type='hidden' name='index' value='{{USER_KEY}}' >

    %# Access
    <input type='hidden' name='total_access' value="{{USER['access']}}" >
    
    <p>Username:
        <input type='text' name='username'
        value="{{USER['name']}}" size='10' onkeyup='GetUserValidation()' {{disabled(USER['name'] == GUEST_USER['name'])}} >
        <small id='validation' ></small>
    </p>
    
    %if USER['name'] != GUEST_USER['name']:
        <p>New Password:
            <input type='password' name='password1'
            value="" size='10' >
            <small>*Use secure password, please!</small>
        </p>
        <p>Repeat New Password:
            <input type='password' name='password2'
            value="" size='10' >
        </p>
    %end
    
    <p>Active:
        <input type='checkbox' name='active' value='1' 
        onclick='GetUserValidation()' {{checked(USER['active'])}} >
    </p>
    <p>Read:
        <input type='checkbox' name='access' value='read'
        onclick="Permissions('read')" {{checked(users.check_access('read', USER))}} >
    </p>
    <p>Write:
        <input type='checkbox' name='access' value='write'
        onclick="Permissions('write')" {{checked(users.check_access('write', USER))}} >
    </p>
    <p>Admin:
        <input type='checkbox' name='access' value='admin'
        onclick="Permissions('admin')" {{checked(users.check_access('admin', USER))}} >
    </p>
    
    %## BUTTONS ##
    <p>
        %if USER_KEY in users.keys():
            %user_index = users.keys().index(USER_KEY)
            %# Up, Down, Remove
            <span class="float_left">
                <input type='button' value='Up' onclick="SubmitAction('admin', 'up')" {{disabled(user_index == 0)}} >
                <input type='button' value='Down' onclick="SubmitAction('admin', 'down')" {{disabled(user_index == len(users)-1)}} >
                <input type='button' value='Remove' onclick="SubmitAction('admin', 'remove')" {{disabled(users.current_user() == USER or USER['name'] == GUEST_USER['name'])}} >
            </span>
            %# Save, Cancel Buttons
            <span class="float_right">
                <input type='submit' name='admin_submit' value='Save' >
                <input type='button' value='Cancel' onclick="CancelForm()" >
            </span>
        %else:
            %# Create, Cancel Buttons
            <span class="float_right">
                <input type='submit' name='admin_submit' value='Create' >
                <input type='button' value='Cancel' onclick="CancelForm()" >
            </span>
        %end
    </p>
    
</fieldset></form>
