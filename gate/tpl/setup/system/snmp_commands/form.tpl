
%### INCLUDES ###
%from gate.main import pages, snmp_agents, snmp_commands
%from gate.snmp import SNMP_COMMAND_TYPES, SNMP_VALUE_TYPES
%from gate.tpl import selected, disabled


%### CONSTANTS ###
%URL = pages.url()
%COMMAND_KEY = pages.get_cookie()['index']
%COMMAND = snmp_commands.get_by_key(COMMAND_KEY)


%### JS ###
<script><!--

%# Initialize agent_name_taken variables
GetSNMPValidation();

function validate_commands_form(form)
{
    if (form.action_method.value == 'update_command')
    {
        if (form.snmp_name.value == "" || form.snmp_name.value == null) 
        {
            alert("SNMP Command name can not be empty!");
            form.snmp_name.focus();
            return false;
        }
        else if (field_name_taken == true)
        {
            alert("This SNMP Command name is taken already!");
            form.snmp_name.focus();
            return false;
        }
        else if (!(/^[0-9.]+$/.test(form.oid.value)))
        {
            alert("Invalid OID!");
            form.oid.focus();
            return false;
        }
        else if ((form.value_type.value == "integer" || form.value_type.value == "timeticks") && !(/^[0-9]+$/.test(form.value.value)))        {
            alert("Command Value must be integer!");
            form.value.focus();
            return false;
        }
        else if (form.value_type.value == "OID" && !(/^[0-9.]+$/.test(form.value.value)))
        {
            alert("Command Value must be in OID format!");
            form.value.focus();
            return false;
        }
        else if (form.value_type.value == "OID" && !(/^[0-9.]+$/.test(form.value.value)))
        {
            alert("Command Value must be in OID format!");
            form.value.focus();
            return false;
        }
        else if (form.value_type.value == "IP address" && !(/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(form.value.value)))
        {
            alert("Command Value must be proper IP Address!");
            form.value.focus();
            return false;
        }
    }
    
    %# Test that JS works properly
    %# alert('Success!')
    return true;
}

//--></script>

%### HTML ###
<form action='/{{URL}}' onsubmit='return validate_commands_form(this)' method='post' ><fieldset>

    %if COMMAND_KEY in snmp_commands.keys():
        <legend><h3>SNMP Command Update</h3></legend>
    %else:
        <legend><h3>New SNMP Command</h3></legend>
    %end
    
    <input type='hidden' name='action_method' value='update_command' >
    <input type='hidden' name='index' value='{{COMMAND_KEY}}' >
    
    <p>Name:
        <input type='text' name='snmp_name'
        value="{{COMMAND['name']}}" size='20' onkeyup="GetSNMPValidation()" >
        <small id='validation' ></small>
    </p>
    <p>Type:       
        <select name='type' >
            %for command_type, command_name in SNMP_COMMAND_TYPES.items():
                <option value='{{command_type}}' {{selected(COMMAND['type'] == command_type)}} >{{command_name}}</option>
            %end
        </select>
    </p>
    <p>OID:
        <input type='text' name='oid' value="{{COMMAND['oid']}}" size='20' >
    </p>
    <p>Value Type:
        <select name='value_type' >
            %for snmp_value_type in SNMP_VALUE_TYPES.keys():
                <option value='{{snmp_value_type}}' {{selected(COMMAND['value_type'] == snmp_value_type)}} >{{snmp_value_type}}</option>
            %end
        </select>
    </p>
    <p>Value:
        <input type='text' name='value' value="{{COMMAND['value']}}" size='20' >
    </p>
    
    %if COMMAND_KEY in snmp_commands.keys():
        <p>Test Command with SNMP Agent:
            <select name='snmp_agent_key'>
                %for snmp_agent_key, snmp_agent in snmp_agents.items():
                    %snmp_agent_index = snmp_agents.keys().index(snmp_agent_key)
                    <option value='{{snmp_agent_key}}' {{selected(snmp_agent_index == 0)}} >{{snmp_agent['name']}}</option>
                %end
            </select>
            <input type='button' value='Test' onclick="SubmitAction('command', 'test_command')" >
        </p>
    %end
    
    %## BUTTONS ##
    <p>
        %if COMMAND_KEY in snmp_commands.keys():
            %command_index = snmp_commands.keys().index(COMMAND_KEY)
            %# Up, Down, Remove
            <span class="float_left">
                <input type='button' value='Up' onclick="SubmitAction('command', 'up')" {{disabled(command_index == 0)}} >
                <input type='button' value='Down' onclick="SubmitAction('command', 'down')" {{disabled(command_index == len(snmp_commands)-1)}} >
                <input type='button' value='Remove' onclick="SubmitAction('command', 'remove')" >
            </span>
            %# Save, Cancel Buttons
            <span class="float_right">
                <input type='submit' name='command_submit' value='Save' >
                <input type='button' value='Cancel' onclick="CancelForm()" >
            </span>
        %else:
            %# Create, Cancel Buttons
            <span class="float_right">
                <input type='submit' name='command_submit' value='Create' >
                <input type='button' value='Cancel' onclick="CancelForm()" >
            </span>
        %end
    </p>
    
</fieldset></form>
