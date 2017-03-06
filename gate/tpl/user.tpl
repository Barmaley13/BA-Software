
%### INCLUDES ###
%import copy

%from gate.main import pages, users
%from gate.web.users import GUEST_USER
%from gate.tpl import disabled


%### CONSTANTS ###
%URL = pages.url()
%USER = users.current_user()

%# Set index for current user. Just in case
%INDEX = None
%for index, user in enumerate(users):
    %if users.current_user() == user:
        %INDEX = pages.set_cookie(index)
    %end
%end

%### JS ###
<script><!--
function validate_user(form)
{
    if (form.action_method.value == 'update')
    {
        if (form.username.value == "" || form.username.value == null) 
        {
            alert("Username can not be empty!");
            form.username.focus();
            return false;
        }
        else if (form.password1.value != form.password2.value)
        {
            alert("Password fields do not match! Try again!");
            form.password1.value = '';
            form.password2.value = '';
            form.password1.focus();
            return false;
        }
        else
        {
            if (user_name_taken == true)
            {
                alert("This username is taken already!");
                form.username.focus();
                return false;
            }
            if (admin_present == false)
            {
                alert("System must have at least one admin!");
                return false;
            }      
        }
    }

    %# Test that JS works properly
    %# alert('Success!')
    return true;
}
//--></script>

%### HTML ###
<div id='form'>
    <form action='/{{URL}}' onsubmit='return validate_user(this)' method='post' ><fieldset>
        <legend><h3>Credentials Update</h3></legend>
        %# Action
        <input type='hidden' name='action_method' value='update_user' >
        %# Index, used by validation
        <input type='hidden' name='index' value='{{INDEX}}' >
        %# Access
        <input type='hidden' name='total_access' value="{{USER['access']}}" >
        
        <p>Username:
            <input type='text' name='username' value="{{USER['name']}}"
            size='10' onkeyup="GetUserValidation()" {{disabled(USER['name'] == GUEST_USER['name'])}} >
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
        
        %# Update, Cancel Buttons
        <p><span class="float_right">
            <input type='submit' name='submit' value='Save' >
            <input type='reset' value='Cancel' >
        </span></p>

    </fieldset></form>
</div>