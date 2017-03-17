
%### INCLUDES ###
%from gate.main import pages, snmp_traps

%from gate.tpl import disabled


%### CONSTANTS ###
%URL = pages.url()
%TRAP_KEY = pages.get_cookie()['index']
%TRAP = snmp_traps[TRAP_KEY]


%### JS ###
<script><!--

%# Initialize agent_name_taken variables
GetNameValidation();

function validate_traps_form(form)
{
    if (form.action_method.value == 'update_trap')
    {
        if (form.snmp_name.value == "" || form.snmp_name.value == null) 
        {
            alert("SNMP Trap name can not be empty!");
            form.snmp_name.focus();
            return false;
        }
        else if (name_taken == true)
        {
            alert("This SNMP Trap name is taken already!");
            form.snmp_name.focus();
            return false;
        }
        else if (!(/^[0-9.]+$/.test(form.oid.value)))
        {
            alert("Invalid OID!");
            form.oid.focus();
            return false;
        }
    }
    
    %# Test that JS works properly
    %# alert('Success!')
    return true;
}

//--></script>

%### HTML ###
<form action='/{{URL}}' onsubmit='return validate_traps_form(this)' method='post' ><fieldset>

    %if TRAP_KEY in snmp_traps.keys():
        <legend><h3>SNMP Trap Update</h3></legend>
    %else:
        <legend><h3>New SNMP Trap</h3></legend>
    %end
    
    <input type='hidden' name='action_method' value='update_trap' >
    <input type='hidden' name='index' value='{{TRAP_KEY}}' >
    
    <p>Name:
        <input type='text' name='snmp_name'
        value="{{TRAP['name']}}" size='20' onkeyup="GetNameValidation()" >
        <small id='name_validation' ></small>
    </p>
    <p>OID:
        <input type='text' name='oid' value="{{TRAP['oid']}}" size='20' >
    </p>
    <p>Value:
        <input type='text' name='value' value="{{TRAP['value']}}" size='20' >
    </p>
       
    %## BUTTONS ##
    <p>
        %if TRAP_KEY in snmp_traps.keys():
            %trap_index = snmp_traps.keys().index(TRAP_KEY)
            %# Up, Down, Remove
            <span class="float_left">
                <input type='button' value='Up' onclick="SubmitAction('trap', 'up')" {{disabled(trap_index == 0)}} >
                <input type='button' value='Down' onclick="SubmitAction('trap', 'down')" {{disabled(trap_index == len(snmp_traps)-1)}} >
                <input type='button' value='Remove' onclick="SubmitAction('trap', 'remove')" >
            </span>
            %# Save, Cancel Buttons
            <span class="float_right">
                <input type='submit' name='trap_submit' value='Save' >
                <input type='button' value='Cancel' onclick="CancelForm()" >
            </span>
        %else:
            %# Create, Cancel Buttons
            <span class="float_right">
                <input type='submit' name='trap_submit' value='Create' >
                <input type='button' value='Cancel' onclick="CancelForm()" >
            </span>
        %end
    </p>
    
</fieldset></form>
