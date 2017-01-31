
%### INCLUDES ###
%import time

%from py_knife import platforms

%from gate.main import system_settings, pages
%from gate.strings import IP_SCHEMES
%from gate.common import TITLE_MAX_LENGTH
%from gate.conversions import get_ip_scheme, get_net_addresses
%from gate.tpl import checked, hidden


%### CONSTANTS ###
%URL = pages.url()
%TIME = system_settings.lcl_time()

%### JS ###
<script><!--
function validate_system_form(form)
{
    var UpdateTimeEnable = Boolean($("[name='system_time']:checked").val() > 0);
    var BrowserTimeEnable = Boolean($("[name='browser_time']:checked").val() > 0);
    
    if (form.title.value == "" || form.title.value == null) 
    {
        alert('System Title can not be empty!');
        form.title.focus();
        return false;
    }
    else if(form.title.value.length > {{TITLE_MAX_LENGTH}})
    {
        alert('System Title is too long!');
        form.title.focus();
        return false;    
    }
    else if(UpdateTimeEnable && BrowserTimeEnable)
    {
        AutoTime();
    }
    
    %# Test that JS works properly
    %# alert('Success!')
    return true;
}
//--></script>

%### HTML ###
%## System Update Form ##
<form action='/{{URL}}' onsubmit='return validate_system_form(this)' method='post' ><fieldset>
    %# Action
    <input type='hidden' name='action_method' value='update_system' >
    %# Epoch Time
    <input type='hidden' name='time' value='' >
    %# Time Zone Offset
    <input type='hidden' name='timezone' value='' >
    %ip_address, subnet_mask = get_net_addresses()
    %# IP Address
    <input type='hidden' name='ip_address' value="{{ip_address}}" >
    %# Subnet Mask
    <input type='hidden' name='subnet_mask' value="{{subnet_mask}}" >
    
    %## SYSTEM TITLE ##
    <p>System Title:
        <input type='text' name='title' value='{{system_settings.title()}}' size='{{TITLE_MAX_LENGTH}}' >
        <small>*Title can be up to {{TITLE_MAX_LENGTH}} characters long</small>
    </p>
    
    %if platforms.PLATFORM in platforms.EMBEDDED_PLATFORMS:
        %## IP ADDRESSING ##
        <p>IP Addressing:
            %ip_scheme = get_ip_scheme()
            <input type='radio' name='ip_scheme' value='dynamic' onchange="HideForm('IpAddress')"
            {{checked(ip_scheme == 'dynamic')}} >{{IP_SCHEMES['dynamic']}}
            <input type='radio' name='ip_scheme' value='static' onchange="DisplayForm('IpAddress')"
            {{checked(ip_scheme == 'static')}} >{{IP_SCHEMES['static']}}
            <small>*Warning: Changes will take effect immediately!</small>
        </p>
        <span id='IpAddress' {{!hidden(ip_scheme == 'dynamic')}} >
            <p>IP Address:
                %for index in range(4):
                    <input type='number' name='ip_address{{index}}' value="{{ip_address.split('.')[index]}}"
                    min='0' max='255' step='1' size='5' onchange="UpdateAddress('ip_address')" >
                %end
            </p>
            <p>Subnet Mask:
                %for index in range(4):
                    <input type='number' name='subnet_mask{{index}}' value="{{subnet_mask.split('.')[index]}}"
                    min='0' max='255' step='1' size='5' onchange="UpdateAddress('subnet_mask')" >
                %end
            </p>
        </span>
        
        %## SYSTEM TIME ##
        <p><b>System Time</b></p>
        <p>Update System Time?
            <input type='radio' name='system_time' value='1' onclick='AutoTime()' >Yes
            <input type='radio' name='system_time' value='0' onclick='AutoTime()' checked >No
            <small>*Note: Remove logs to speed up this procedure!</small>
        </p>
        <span id='SystemTime' class='hidden' >
            <p>Use your Browser Time?
                <input type='radio' name='browser_time' value='1' onchange='AutoTime()' checked >Yes
                <input type='radio' name='browser_time' value='0' onchange='AutoTime()' >No
            </p>
            <table class='hor-minimalist-b'>
                <thead><tr>
                    <th>Year</th>
                    <th>Month</th>
                    <th>Day</th>
                    <th>Hours</th>
                    <th>Minutes</th>
                    <th>Seconds</th>
                </tr></thead>
                <tr>
                    <td>
                        <input type='number' name='year' value="{{time.strftime('%Y', time.gmtime(TIME))}}"
                        min='2000' max='2500' step='1' size='5' onchange='UpdateTime()' disabled >
                    </td>
                    <td>
                        <input type='number' name='month' value="{{time.strftime('%m', time.gmtime(TIME))}}"
                        min='1' max='12' step='1' size='5' onchange='UpdateTime()' disabled >
                    </td>
                    <td>
                        <input type='number' name='day' value="{{time.strftime('%d', time.gmtime(TIME))}}"
                        min='1' max='31' step='1' size='5' onchange='UpdateTime()' disabled >
                    </td>
                    <td>
                        <input type='number' name='hours' value="{{time.strftime('%H', time.gmtime(TIME))}}"
                        min='0' max='23' step='1' size='5' onchange='UpdateTime()' disabled >
                    </td>
                    <td>
                        <input type='number' name='minutes' value="{{time.strftime('%M', time.gmtime(TIME))}}"
                        min='0' max='59' step='1' size='5' onchange='UpdateTime()' disabled >
                    </td>
                    <td>
                        <input type='number' name='seconds' value="{{time.strftime('%S', time.gmtime(TIME))}}"
                        min='0' max='59' step='1' size='5' onchange='UpdateTime()' disabled >
                    </td>
                </tr>
            </table>
        </span>
        %"""
        <p>Timezone:
            <input type='number' name='timezone' value="{{system_settings['timezone']}}"
            min='-12' max='14' step='1' size='5' onchange='UpdateTime()' >
            <small>*Updating timezone will not affect internal timing (System is using UTC)</small>
        </p>
        %"""
    %end
    
    %## LOG OPTIONS ##
    <p><b>Log Options</b></p>
    <p>Log Limit:
        <input type='number' name='log_limit' value="{{system_settings['log_limit']}}" min='50' max='1000' step='1' size='5' >
        <small>*Recommended value: 100 points</small>
    </p>

    %## WARNINGS ##
    <p><b>Warning Settings </b><p>
    <p>Warnings Pop Up Enable:
        <input type='checkbox' name='warnings_pop_up_enable' value='1' {{checked(system_settings['warnings_pop_up_enable'])}} >
    </p>
    <p>Warnings Sound Enable:
        <input type='checkbox' name='warnings_sound_enable' value='1' {{checked(system_settings['warnings_sound_enable'])}} >
    </p>
    
    %## BUTTONS ##
    <p>
        %# Update, Reset, Cancel Buttons
        <span class="float_right">
            <input type='submit' name='submit' value='Save' >
            <input type='button' value='Cancel' onclick='CancelForm()' >
        </span>
    </p>

</fieldset></form>
