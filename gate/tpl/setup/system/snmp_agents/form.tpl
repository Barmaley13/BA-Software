
%### INCLUDES ###
%from gate.main import pages, snmp_agents
%from gate.snmp import SNMP_COMMUNITY, SNMP_VERSIONS
%from gate.tpl import selected, disabled


%### CONSTANTS ###
%URL = pages.url()
%AGENT_KEY = pages.get_cookie()['index']
%AGENT = snmp_agents.get_by_key(AGENT_KEY)


%### JS ###
<script><!--

%# Initialize field_name_taken variables
GetSNMPValidation();

function validate_agents_form(form)
{
    if (form.action_method.value == 'update_agent')
    {
        if (form.snmp_name.value == "" || form.snmp_name.value == null) 
        {
            alert("SNMP Agent name can not be empty!");
            form.snmp_name.focus();
            return false;
        }
        else if (field_name_taken == true)
        {
            alert("This SNMP Agent name is taken already!");
            form.snmp_name.focus();
            return false;
        }
        else if (form.ip_address3.value == 255)
        {
            alert("Sorry, SNMP broadcast is not supported! Please, change last digit of the IP Address to something other than 255!");
            form.ip_address3.focus();
            return false;
        }
    }
    
    %# Test that JS works properly
    %# alert('Success!')
    return true;
}

//--></script>


%### HTML ###
<form action='/{{URL}}' onsubmit='return validate_agents_form(this)' method='post' ><fieldset>

    %if AGENT_KEY in snmp_agents.keys():
        <legend><h3>SNMP Agent Update</h3></legend>
    %else:
        <legend><h3>New SNMP Agent</h3></legend>
    %end
    
    <input type='hidden' name='action_method' value='update_agent' >
    <input type='hidden' name='index' value='{{AGENT_KEY}}' >
    <input type='hidden' name='ip_address' value="{{AGENT['ip_address']}}" >
    
    <p>Name:
        <input type='text' name='snmp_name'
        value="{{AGENT['name']}}" size='20' onkeyup="GetSNMPValidation()" >
        <small id='validation' ></small>
    </p>
    <p>IP Address:
        %for index in range(4):
            <input type='number' name='ip_address{{index}}' value="{{AGENT['ip_address'].split('.')[index]}}"
            min='0' max='255' step='1' size='5' onchange="UpdateAddress('ip_address')" >
        %end
    </p>
    <p>Port:
        <input type='number' name='port' value="{{AGENT['port']}}"
        min='0' max='65535' step='1' size='5' >
    </p>
    <p>SNMP Community:
        <select name='snmp_community' >
            %for community in SNMP_COMMUNITY:
                <option value='{{community}}' {{selected(AGENT['snmp_community'] == community)}} >{{community}}</option>
            %end
        </select>
    </p>
    <p>SNMP Version:
        <select name='snmp_version' >
            %for version_index, version in enumerate(SNMP_VERSIONS):
                <option value='{{version_index}}' {{selected(AGENT['snmp_version'] == version_index)}} >{{version}}</option>
            %end
        </select>
    </p>    
    
    %## BUTTONS ##
    <p>
        %if AGENT_KEY in snmp_agents.keys():
            %agent_index = snmp_agents.keys().index(AGENT_KEY)
            %# Up, Down, Remove
            <span class="float_left">
                <input type='button' value='Up' onclick="SubmitAction('agent', 'up')" {{disabled(agent_index == 0)}} >
                <input type='button' value='Down' onclick="SubmitAction('agent', 'down')" {{disabled(agent_index == len(snmp_agents)-1)}} >
                <input type='button' value='Remove' onclick="SubmitAction('agent', 'remove')" >
            </span>
            %# Save, Test, Cancel Buttons
            <span class="float_right">
                <input type='submit' name='agent_submit' value='Save' >
                <input type='button' value='Test' onclick="SubmitAction('agent', 'test_agent')" >
                <input type='button' value='Cancel' onclick="CancelForm()" >
            </span>
        %else:
            %# Create, Cancel Buttons
            <span class="float_right">
                <input type='submit' name='agent_submit' value='Create' >
                <input type='button' value='Cancel' onclick="CancelForm()" >
            </span>
        %end
    </p>
    
</fieldset></form>
