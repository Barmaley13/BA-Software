
%### INCLUDES ###
%from bottle import template

%from gate.main import manager, pages
%from gate.conversions import CYCLES_MAX_INT, TIMEOUT_MAX_FLOAT


%### CONSTANTS ###
%URL = pages.url()
%COOKIE = pages.get_cookie()
%INDEX = None
%if 'index' in COOKIE:
    %INDEX = pages.get_cookie()['index']
    %NETWORK = manager.networks[INDEX]
%end


%### JS ###
%if INDEX is not None:
    <script><!--
    function validate_network_form(form)
    {
        var confirmation = true;
        %# Simple form validator
        var hex = /^([A-Fa-f0-9])+$/;

        %# Number Validation
        var i;
        var NumArray = [
            ['wake', 'Wake Period', {{CYCLES_MAX_INT}}],
            ['sleep', 'Sleep Period', {{CYCLES_MAX_INT}}],
            ['timeout_wake', 'Timeout Wake Period', {{int(TIMEOUT_MAX_FLOAT)}}],
            ['timeout_sleep', 'Timeout Sleep Period', {{int(TIMEOUT_MAX_FLOAT)}}]
        ];
        
        if (form.action_method.value == 'update_network')
        {   
            
            %"""
            if (form.net_id.value == "" || form.net_id.value == null)
            {
                alert("Network ID can not be empty!");
                form.net_id.focus();
                return false;
            }
            else if(form.net_id.value.length != 4)
            {
                alert("Network ID has to be 4 digits!");
                form.net_id.focus();
                return false;
            }
            else if(hex.test(form.net_id.value)==false)
            {
                alert("Network ID contains invalid characters!");
                form.net_id.focus();
                return false;
            }
            else if(form.aes_enable[0].checked)
            %"""
            if(form.aes_enable[0].checked)
            {
                if(form.aes_key.value.length > 16)
                {
                    alert("AES Key can not be longer than 16 characters!");
                    form.aes_key.focus();
                    return false;
                }
            }
            else if(form.wake.value == 0)
            {
                alert("Wake Period can not be zero!");
                form.wake.focus();
                return false;
            }
            else if(form.sleep.value <= 30)
            {
                confirmation = confirm("Sleep period is 30 seconds or less. Are you sure you want to save the value? This might drastically reduce battery lives of the field units!");
            }
            
            %# Number Validation
            for(i=0; i<NumArray.length; i++)
            {
                if(form[NumArray[i][0]].value == 0)
                {
                    alert(NumArray[i][1] + " can not be zero!");
                    form[NumArray[i][0]].focus();
                    return false;
                }
                else if(form[NumArray[i][0]].value >= NumArray[i][2])
                {
                    form[NumArray[i][0]].value = NumArray[i][2];
                    alert(NumArray[i][1] + " was set to maximum value!");
                }
            }
            
            if (confirmation)
            {
                %# Reenable Fields (Otherwise those wont be passed by php)
                form.timeout_wake.disabled = false;
                form.timeout_sleep.disabled = false;
            }

        }
        else if(form.action_method.value != 'remove' && form.action_method.value != 'restore')
        {   
            %# Do nothing cases
            var up_validation = (form.action_method.value == 'up' && form.index.value > 0);
            var down_validation = (form.action_method.value == 'down' && form.index.value < ($("input:radio[name='index']").length - 1));
            
            if (!up_validation && !down_validation)
            {
                return false;
            }
        }

        %# Test that JS works properly
        %# alert('Success!')
        return confirmation;
    }
    //--></script>
        
    %### HTML ###
    %## Network Update Form ##
    <form action='/{{URL}}' onsubmit='return validate_network_form(this)' method='post' ><fieldset>
        <input type='hidden' name='action_method' value='update_network' >
        <input type='hidden' name='index' value='{{INDEX}}' >

        %"""
        <p>Network ID:
            <input type='text' name='net_id' value='{{NETWORK['net_id']}}' size='6' >
            <small>*Enter 4 HEX Digits. Valid Characters: 0-9, a-e, A-E</small>
        </p>
        %"""
        %# Network Parameters
        {{!pages.template_html('setup_page', 'network_html', network = NETWORK)}}
        <p>Autofill Timeout Parameters?
            <input type='radio' name='autofill_enable' value='1' checked onchange='AutoTimeout()' >Yes
            <input type='radio' name='autofill_enable' value='0' onchange='AutoTimeout()' >No
        </p>
        %# Sleep, Wake, TO Sleep and TO Wake Table
        <table class='hor-minimalist-b'>
            %# Headers
            <thead>
                <tr>
                    <th scope='col'>Wake Period, seconds</th>
                    <th scope='col'>Sleep Period, seconds</th>
                    <th scope='col'>Timeout Wake Period, seconds</th>
                    <th scope='col'>Timeout Sleep Period, seconds</th>
                </tr>
            </thead>
            %# Input Fields
            <tr> 
                <td>
                    <input type='number' name='wake' value="{{NETWORK['wake']}}"
                    min='0.5' max='{{CYCLES_MAX_INT}}' step='0.01' size='5' onchange='AutoTimeoutValues()' >
                </td>
                <td>
                    <input type='number' name='sleep' value="{{NETWORK['sleep']}}"
                    min='5' max='{{CYCLES_MAX_INT}}' step='0.01' size='5' onchange='AutoTimeoutValues()' >
                </td>
                <td>
                    <input type='number' name='timeout_wake' value="{{NETWORK['timeout_wake']}}"
                    min='0' max='{{int(TIMEOUT_MAX_FLOAT)}}' step='0.01' size='5' disabled >
                </td>
                <td>
                    <input type='number' name='timeout_sleep' value="{{NETWORK['timeout_sleep']}}"
                    min='0' max='{{int(TIMEOUT_MAX_FLOAT)}}' step='0.01' size='5' disabled >
                </td>
            </tr>
        </table>

        %## BUTTONS ##
        <p>
            %# Restore to Defaults
            <span class="float_left">
                <input type='button' value='Restore to Defaults' onclick="SubmitAction('network', 'restore')" >
            </span>
            %# Update, Reset, Cancel Buttons
            <span class="float_right">
                <input type='submit' name='network_submit' value='Save' >
                <input type='button' value='Cancel' onclick="CancelForm()" >
            </span>
        </p>

    </fieldset></form>
%end
