
%### INCLUDES ###
%from gate.main import pages


%### HTML ###
<form action='/{{pages.url()}}' method='post' ><fieldset>
    %# Action
    %# <input type='hidden' name='action_method' value='update_snmp' >

    <p><b>SNMP Agents</b><p>
        {{!pages.template_html('snmp_agents', 'table', table_only=True)}}
        <p><input type="button" onclick="location.href='/{{pages.url('snmp_agents')}}'" value="Edit SNMP Agents"></p>
    
    <p><b>SNMP Commands</b><p>
        {{!pages.template_html('snmp_commands', 'table', table_only=True)}}    
        <p><input type="button" onclick="location.href='/{{pages.url('snmp_commands')}}'" value="Edit SNMP Commands"></p>    

    <p><b>SNMP Traps</b><p>
        {{!pages.template_html('snmp_traps', 'table', table_only=True)}}    
        <p><input type="button" onclick="location.href='/{{pages.url('snmp_traps')}}'" value="Edit SNMP Traps"></p>

    <p><b>SNMP Alerts and Acks</b><p>
        <p><input type="button" onclick="location.href='/{{pages.url('alerts_acks')}}'" value="Edit SNMP Alerts and Acks"></p>
    
    %## BUTTONS ##
    <p>
        %# Update, Reset, Cancel Buttons
        <span class="float_right">
            %# <input type='submit' name='submit' value='Save' >
            <input type='button' value='Cancel' onclick="CancelForm()" >
        </span>
    </p>

</fieldset></form>
