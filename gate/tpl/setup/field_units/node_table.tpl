
%### INCLUDES ###
%from gate.main import system_settings, pages
%from gate.tpl import checked


%### CONSTANTS ###
%ADDRESS = pages.get_cookie()

%GROUP = None
%if not defined('group'):
    %if ADDRESS['group'] is not None:
        %GROUP = pages.platforms.group(ADDRESS)
    %end
%else:
    %GROUP = group
%end


%### FUNCTIONS ###
%def generate_buttons():
    %if not defined('group'):
        <p><span class="float_right">
            <input type='button' value='Back' onclick="GoBack()" >
        </span></p>
    %end
%end


%### HTML ###
%if GROUP and len(GROUP.nodes):
    %if system_settings.name == 'jowa':
        %generate_buttons()
    %end
    
    <table class='hor-minimalist-b'>
        %# Static Header Names #
        <thead><tr>
            %# Select Field for id
            %if not defined('group'):
                <th scope='col'>
                    <input type='checkbox' name='net_addr_all' onchange='CheckAll()' >
                </th>
            %end
            <th scope='col'>Name</th>
            <th scope='col'>MAC Address</th>
            %#<th scope='col'>Net Address</th>
            %if system_settings.modbus_enable:
                <th scope='col'>Modbus Address</th>
            %end
            %if not defined('group'):
                <th scope='col'>Presence</th>
            %end
            <th scope='col'>Platform</th>
            <th scope='col'>Firmware</th>
            <th scope='col'>Software</th>
            %if not defined('group'):
                <th scope='col'>Last Sync</th>
                <th scope='col'>Created</th>
            %end
        </tr></thead>
        
        <input type='hidden' name='platform' value="{{ADDRESS['platform']}}" >
        <input type='hidden' name='group' value="{{ADDRESS['group']}}" >
        
        %# Table Data #
        %for node in GROUP.nodes.values():
            <tr>
                %if not defined('group'):
                    <td>
                        %checkbox_status = bool('nodes' in ADDRESS and node['net_addr'] in ADDRESS['nodes'])
                        <input type='checkbox' name='net_addr' value="{{node['net_addr']}}" onchange="CheckNode()"
                        {{checked(checkbox_status)}} >
                        %if not checkbox_status:
                            <input type='hidden' name='node_name' value="{{node['name']}}" >
                        %end                        
                    </td>
                %end
                <td>{{node['name']}}</td>
                <td>{{node['mac']}}</td>
                %#<td>{{node['net_addr']}}</td>
                %if system_settings.modbus_enable:
                    <td>{{node['modbus_addr']}}</td>
                %end
                %if not defined('group'):
                    <td>{{bool(node['presence'])}}</td>
                %end
                <td>{{node['raw_platform']}}</td>
                <td>{{node['firmware']}}</td>
                <td>{{node['software']}}</td>
                %if not defined('group'):
                    <td>{{node.last_sync()}}</td>
                    <td>{{node.created()}}</td>
                %end
            </tr>
        %end
    </table>
    
    %if system_settings.name != 'jowa':
        %generate_buttons()
    %end
        
    %## Check All Nodes Checkbox Init ##
    %if 'nodes' in ADDRESS:
        <script><!--
            UpdateCheckAll({{len(ADDRESS['nodes'])}});
        //--></script>
    %end
%end
