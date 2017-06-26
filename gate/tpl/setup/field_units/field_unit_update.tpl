
%### INCLUDES ###
%import logging
%from bottle import template

%from gate.main import manager, pages, users
%from gate.modbus import MODBUS_REG_NUM
%from gate.tpl import hidden, selected, disabled


%### CONSTANTS ###
%if not defined('url'):
    %url = '/' + pages.url()
%end
%ADDRESS = pages.get_cookie('nodes_subpage')
%PLATFORM = pages.platforms.platform(ADDRESS)
%NODE = pages.platforms.node(ADDRESS)
%INACTIVE_GROUP = bool(ADDRESS['group'] == PLATFORM.groups.keys()[0])

%MODBUS_ADDRESSES_SELECTION_NUMBER = 100

%## Logger ##
%LOGGER = logging.getLogger(__name__)
%# LOGGER.setLevel(logging.DEBUG)


%### JS ###
<script><!--
    function validate_update_node_form(form)
    {
        %# Simple form validator
        %# var hex = /^([A-Fa-f0-9])+$/;
    
        if (form.action_method.value == 'update_node')
        {
        
        %if 'nodes' in ADDRESS and len(ADDRESS['nodes']) == 1:
            if (form.node_name.value == "" || form.node_name.value == null)
            {
                alert("Node Name can not be empty!");
                form.node_name.focus();
                return false;
            }
            %if not INACTIVE_GROUP:
                %modbus_addresses = manager.nodes.modbus_addresses()
                %if NODE['modbus_addr'] in modbus_addresses:
                    %current_index = modbus_addresses.index(NODE['modbus_addr'])
                    %del modbus_addresses[current_index]
                %end
                else if ($.inArray(Number(form.modbus_addr.value), {{str(modbus_addresses)}}) != -1)
                {
                    alert("Modbus address '" + form.modbus_addr.value + "' is taken already! Please select modbus address that is currently open!");
                    return false;
                }
            %end
            %"""
            else if (form.mac.value.length != 16) 
            {
                alert("MAC Address has to be 16 digits!");
                form.mac.focus();
                return false;
            }
            else if (hex.test(form.mac.value)==false) 
            {
                alert("MAC Address contains invalid characters!");
                form.mac.focus();
                return false;
            }
            %"""
        %end
        %if INACTIVE_GROUP:
            if(form.aes_enable[0].checked)
            {
                if(form.aes_key.value.length > 16)
                {
                    alert("AES Key can not be longer than 16 characters!");
                    form.aes_key.focus();
                    return false;
                }
            }
        %end
            if ($("input:hidden[name='node_name']").length > 0)
            {
                var user_answer = null;
                $("input:hidden[name='node_name']").each(function () {
                    if ($(this).val() == form.node_name.value)
                    {
                        if (user_answer == null)
                            user_answer = confirm("This name is already in use! Would you like to proceed?");
                    }
                });
                if (user_answer == null)
                    user_answer = true
                return user_answer;
            }
        }
        
        %# Test that JS works properly
        %# alert('Success!');
        return true;
    }
   
    function SelectGroup()
    {
        var group_name = $("select[name='new_group']").find(":selected").val();
        if (group_name != "{{PLATFORM.groups.keys()[0]}}")
        {
            $("select[name='channel']").prop('disabled', true);
            $("select[name='data_rate']").prop('disabled', true);
            $("input[name='aes_enable']").prop('disabled', true);
            $("input[name='aes_key']").prop('disabled', true);
        }
        else
        {
            $("select[name='channel']").prop('disabled', false);
            $("select[name='data_rate']").prop('disabled', false);
            $("input[name='aes_enable']").prop('disabled', false);
            $("input[name='aes_key']").prop('disabled', false);
        }
    }
    
//--></script>

%### HTML ###
%## Node Update Form ##
<form action='{{url}}' onsubmit='return validate_update_node_form(this)' method='post' name='update_node_form' ><fieldset>
    %## FORM FIELDS ##
    <input type='hidden' name='action_method' value='update_node' >
    
    <input type='hidden' name='platform' value="{{ADDRESS['platform']}}" >
    <input type='hidden' name='group' value="{{ADDRESS['group']}}" >

    %## INPUT FIELDS ##
    %node_name = 'Multiple'
    %if len(ADDRESS['nodes']) == 1:
        %node_name = NODE['name']
    %end
    
    <p>Name:
        <input type='text' name='node_name' value='{{node_name}}' size='10' {{disabled(len(ADDRESS['nodes']) > 1)}} >
    </p>
    
    %"""
    <p>MAC Address:
        <input type='text' name='mac_str' value="{{NODE['mac']}}" size='18' >
        <small>*Enter 16 HEX Digits. Valid Characters: 0-9, a-e, A-E</small>
    </p>
    %"""
        
    <p>Group:
        <select name='new_group' >
            %for group_name, group in PLATFORM.groups.items():
                <option value='{{group_name}}' {{selected(group_name == ADDRESS['group'])}} >
                    {{group['name']}}
                </option>
            %end
        </select>
    </p>

    %if not INACTIVE_GROUP:
        %modbus_addr = 'Multiple'
        <p>Modbus Address:
        %if len(ADDRESS['nodes']) == 1:
            %modbus_addr = NODE['modbus_addr']
            <input type='number' name='modbus_addr' value='{{modbus_addr}}' 
            min='0' max='{{MODBUS_ADDRESSES_SELECTION_NUMBER*MODBUS_REG_NUM}}' step='{{MODBUS_REG_NUM}}' size='5' >
        %else:
            <input type='text' name='modbus_addr' value='{{modbus_addr}}' {{disabled(True)}} >
        %end
        </p>
        
        %## ADC ENABLES ##
        <p><b>ADC Alarms and Enables</b></p>
        %# Display ADC Enables
        <input type='hidden' name='total_display' value="" >
        %# Track ADC Enables
        <input type='hidden' name='total_track' value="" >
        %# Diagnostic Header Enables
        <input type='hidden' name='total_diagnostics' value="" >
        %# ADC Alarm
        <input type='hidden' name='total_min_alarm' value="" >
        <input type='hidden' name='total_max_alarm' value="" >
        
        {{!pages.platforms.headers_html(ADDRESS)}}

    %else:
        %## NETWORK SETTINGS ##
        <p><b>Network Settings</b></p>
        <p><small>*Enter known parameters otherwise field unit might be lost!</small></p>
        {{!pages.template_html('setup_page', 'network_html', network = manager.networks[0])}}
        <script><!--
            $("select[name='new_group']").change(function(){SelectGroup()});
        //--></script>
    %end
    
    %# Debugging
    %"""
    %for net_addr in ADDRESS['nodes']:
        %LOGGER.debug("*** NET_ADDR = " + net_addr + " ***")
        %node = pages.platforms.node(ADDRESS, net_addr)
        %display_headers = PLATFORM.headers.read('display').values()
        %for header in display_headers:
            %LOGGER.debug(header['name'] + ": display = " + str(header.enables(node, 'live_enable')) + " track = " + str(header.enables(node, 'log_enable')))
        %end
    %end
    %"""
    
    %## BUTTONS ##
    <p>
        %if users.check_access('write'):
            <span class="float_left">
                %nodes = pages.platforms.group(ADDRESS).nodes
                %if len(nodes):
                    %net_addr = ADDRESS['nodes'][0]
                    %index = nodes.keys().index(net_addr)
                    <input type='button' value='Up' onclick="SubmitAction('node_update', 'up')" {{disabled(index == 0 or len(ADDRESS['nodes']) > 1)}} >
                    <input type='button' value='Down' onclick="SubmitAction('node_update', 'down')" {{disabled(index == len(nodes)-1 or len(ADDRESS['nodes']) > 1)}} >
                    <input type='button' value='Remove' onclick="SubmitAction('node_update', 'remove')" >
                %end
            </span>
            <span class="float_right">
                <input type='submit' name='node_update_submit' value='Save' >
        %else:
            <span class="float_right">
        %end
            <input type='button' value='Cancel' onclick="GoCancel()" >
        </span>
    </p>

</fieldset></form>
