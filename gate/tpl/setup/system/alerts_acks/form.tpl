
%### INCLUDES ###
%import copy

%from py_knife.ordered_dict import OrderedDict

%from gate.main import pages, snmp_agents, snmp_commands, snmp_traps
%from gate.tpl import selected, disabled


%### CONSTANTS ###
%URL = pages.url()
%ADDRESS = pages.get_cookie()
%ACTIVE_PLATFORMS = pages.platforms.active_platforms()

%ALERT_GROUPS = OrderedDict()
%ALERT_GROUPS['hardware'] = 'Hardware Warnings'
%ALERT_GROUPS['sensor_fault'] = 'Sensor Fault Warnings'
%ALERT_GROUPS['alarms'] = 'Alarm Warnings'
%ALERT_GROUPS['diagnostics'] = 'Diagnostic Warnings'

%SNMP_COLUMNS = OrderedDict()
%SNMP_COLUMNS['agent'] = snmp_agents
%SNMP_COLUMNS['set'] = snmp_commands
%SNMP_COLUMNS['clear'] = snmp_commands
%SNMP_COLUMNS['trap'] = snmp_traps


%### FUNCTIONS ###
%def generate_warnings_row(warning_description, td_group='', tr_groups=None, alert_key=None, snmp_dict=None):
    %if tr_groups is None:
        %tr_groups = []
    %end
    %tr_groups_str = ' '.join(tr_groups)

    <tr class='{{tr_groups_str}}'>
        <td class='{{td_group}}'>{{warning_description}}</td>
        
        %for snmp_column_name, snmp_items in SNMP_COLUMNS.items():
            <td>
                %if alert_key is None:
                    <select name="{{snmp_column_name}}" class='{{td_group}}' onchange="UpdateWarnings('{{snmp_column_name}}', '{{td_group}}')" >
                %else:
                    <select name="{{alert_key + '-' + snmp_column_name}}" onchange="UpdateGroups('{{snmp_column_name}}', '{{tr_groups_str}}')" >
                %end
                    
                    %"""
                    %if snmp_dict is not None:
                        %print('LOAD: {} : {}'.format(alert_key, [snmp_column_name]))
                    %end
                    %"""

                    <option value=''>None</option>
                    %for snmp_item_key, snmp_item in snmp_items.items():
                        %selected_snmp_item = bool(snmp_dict is not None) and bool(snmp_dict[snmp_column_name] is not None) and bool(snmp_dict[snmp_column_name] == snmp_item_key)
                        <option value='{{snmp_item_key}}' {{selected(selected_snmp_item)}} >{{snmp_item['name']}}</option>
                    %end
                    
                </select>
            </td>
        %end
        
    </tr>
%end


%### HTML ###
%if len(ACTIVE_PLATFORMS):
    <form action='/{{URL}}' method='post' ><fieldset>
        %## LEGEND ##
        %legend = ''
        %if 'nodes' in ADDRESS:
            %target = pages.platforms.node(ADDRESS)
            %legend = " of field unit '" + target['name'] + "'"
        %elif 'group' in ADDRESS:
            %target = pages.platforms.group(ADDRESS)
            %legend = " of group '" + target['name'] + "'"
        %else:
            %if 'platform' in ADDRESS:
                %target = pages.platforms.platform(ADDRESS)
            %else:
                %target = ACTIVE_PLATFORMS.values()[0]
            %end            
            %if len(ACTIVE_PLATFORMS) > 1:
                %legend = " of platform '" + target['name'] + "'"
            %end
        %end
        
        <legend><h3>SNMP Alert and Acks Update{{legend}}</h3></legend>
        
        <input type='hidden' name='action_method' value='update' >
        
        %## SNMP SELECTIONS ##
        <table class='hor-minimalist-b'>
            %# Static Header Names #
            <thead><tr>
                %# Select field for user id
                <th scope='col'>Warning Description</th>
                <th scope='col'>SNMP Agent</th>
                <th scope='col'>SNMP Alert Set Command</th>
                <th scope='col'>SNMP Alert Clear Command</th>
                <th scope='col'>SNMP Ack Trap</th>
            </tr></thead>

            %# Table Data #
            %# Generate HTML
            %all_groups = ['all_warnings']
            %generate_warnings_row('All Warnings', all_groups[-1])
            %unique_groups = list(set([])|set(all_groups))
            
            %for alert_group_key, alert_group_name in ALERT_GROUPS.items():
                %alert_groups = copy.deepcopy(all_groups)
                %alert_groups.append(alert_group_key + '_warnings')
                %# Generate Group
                %generate_warnings_row(alert_group_name, alert_groups[-1], all_groups)
                
                %# Generate Alerts in a group
                %alert_messages = target.headers.alert_messages(alert_group_key)            
                %for alert_key, alert_message in alert_messages.items():
                    %alert_key_list = alert_key.split('-')
                    %error_field = alert_key_list[0]
                    %error_code = alert_key_list[1]
                    %snmp_dict = target.error.get_snmp(error_field, error_code)
                    %# print('snmp_dict: {}'.format(snmp_dict))
                    %generate_warnings_row(alert_message, '', alert_groups, alert_key, snmp_dict)
                %end
                
                %unique_groups = list(set(unique_groups)|set(alert_groups))
            %end
            
        </table>
        
        %## BUTTONS ##
        <p>
            %# Save, Cancel Buttons
            <span class="float_right">
                <input type='submit' name='submit' value='Save' >
                <input type='button' value='Cancel' onclick='GoForward()' >
            </span>
        </p>
        
    </fieldset></form>

    %### JS ###
    %# Initialize collapsible lists and regenerate group values
    <script><!--
        %for group_name in unique_groups:
            CreateGroup('{{group_name}}');
        %end
        %group_names = ' '.join(unique_groups)
        %for snmp_column_name in SNMP_COLUMNS.keys():
            UpdateGroups('{{snmp_column_name}}', '{{group_names}}');
        %end
    //--></script>

%end
