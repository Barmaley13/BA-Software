
%### INCLUDES ###
%from gate.main import pages

%### CONSTANTS ###
%URL = pages.url()
%"""
%if URL == pages.url('login_page'):
    %URL = pages.url('live_data')
%end
%"""


%### JS ###
<script><!--
function validate_login_form(form)
{ 
    if (form.username.value == "" || form.username.value == null)
    {
        alert("Username can not be empty!");
        form.username.focus();
        return false;
    }
    else if (form.password.value == "" || form.password.value == null)
    {
        alert("Password can not be empty!");
        form.password.focus();
        return false;
    }

    %# Test that JS works properly
    %# alert('Success!')
    return true;
}
//--></script>

%### HTML ###
<form action='/{{URL}}' onsubmit='return validate_login_form(this)' method='post' ><fieldset>
    <legend><h3>Enter your Credentials</h3></legend>
    %# Action Type
    <input type='hidden' name='action_method' value='login_user' >
    %# Username
    <p>Username: <input type='text' name='username' size='20' ></p>
    %# Password
    <p>Password: <input type='password' name='password' size='20' ></p>
    %#  Submit, Cancel Buttons
    <p><span class="float_right">
        <input type='submit' name='submit' value='Submit'>
        <input type='reset' name='reset' value='Cancel'>
    </span></p>

</fieldset></form>
